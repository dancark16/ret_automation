from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Retencion
from app.services.pdf_extractor import extract_from_bytes
from app.config import settings

router = APIRouter(prefix="/api/sri", tags=["sri"])


async def _descargar_y_registrar(db_factory, ruc: str, password: str):
    from playwright.async_api import async_playwright

    db = next(db_factory())
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()

            # Login SRI
            await page.goto("https://srienlinea.sri.gob.ec/sri-en-linea/inicio/NAT")
            await page.fill('input[name="usuario"]', ruc)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_load_state("networkidle")

            # Navegar a comprobantes recibidos
            await page.goto(
                "https://srienlinea.sri.gob.ec/comprobantes-electronicos-internet"
                "/pages/consultas/receptor.jsf"
            )
            await page.wait_for_load_state("networkidle")

            # Filtrar por Retención — AJUSTA estos selectores la primera vez con headless=False
            await page.select_option('select[id*="tipoComprobante"]', label="RETENCIÓN EN LA FUENTE")
            await page.click('button[id*="buscar"]')
            await page.wait_for_load_state("networkidle")

            rows = await page.query_selector_all('tr[class*="rich-table-row"]')
            nuevas = 0
            for row in rows:
                auth_el = await row.query_selector('td:nth-child(3)')
                if not auth_el:
                    continue
                auth_num = (await auth_el.inner_text()).strip()

                existente = db.query(Retencion).filter_by(ret_number=auth_num).first()
                if existente:
                    continue

                pdf_btn = await row.query_selector('a[title*="PDF"], a[title*="pdf"]')
                if not pdf_btn:
                    continue

                async with context.expect_download() as dl:
                    await pdf_btn.click()
                download = await dl.value
                pdf_bytes = open(await download.path(), "rb").read()

                try:
                    data = extract_from_bytes(pdf_bytes)
                except Exception:
                    continue

                r = Retencion(
                    ret_number=data.ret_number,
                    ret_serial=data.ret_serial,
                    client_name=data.client_name,
                    invoice_sequential=data.invoice_sequential,
                    invoice_date=data.invoice_date,
                    renta_pct=data.renta_pct,
                    renta_base=data.renta_base,
                    renta_value=data.renta_value,
                    iva_pct=data.iva_pct,
                    iva_base=data.iva_base,
                    iva_value=data.iva_value,
                    pdf_bytes=pdf_bytes,
                )
                db.add(r)
                nuevas += 1

            db.commit()
            await browser.close()
            return nuevas
    finally:
        db.close()


@router.post("/sincronizar")
async def sincronizar(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not settings.SRI_RUC or not settings.SRI_PASSWORD:
        return {"ok": False, "mensaje": "Credenciales SRI no configuradas en .env"}

    background_tasks.add_task(
        _descargar_y_registrar,
        lambda: iter([db]),
        settings.SRI_RUC,
        settings.SRI_PASSWORD,
    )
    return {"ok": True, "mensaje": "Sincronización iniciada en segundo plano"}
