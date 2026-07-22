"""
Descarga retenciones del portal SRI (srienlinea.sri.gob.ec).
Requiere playwright: playwright install chromium
"""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from config import SRI_RUC, SRI_PASSWORD, DOWNLOADS_PATH

SRI_URL = "https://srienlinea.sri.gob.ec/sri-en-linea/inicio/NAT"


def download_new_retentions(processed_ids: set) -> list[Path]:
    """
    Ingresa al SRI, descarga los comprobantes de retención no procesados.
    Devuelve lista de paths de PDFs descargados.
    """
    downloaded = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=True cuando esté estable
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # Login
        page.goto(SRI_URL)
        page.fill('input[name="usuario"]', SRI_RUC)
        page.fill('input[name="password"]', SRI_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Navegar a comprobantes electrónicos recibidos
        # NOTA: La navegación exacta depende del portal SRI actual.
        # Debes verificar los selectores con headless=False la primera vez.
        page.goto("https://srienlinea.sri.gob.ec/comprobantes-electronicos-internet/pages/consultas/receptor.jsf")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Filtrar por tipo "Retención"
        # Ajusta estos selectores según lo que veas en el portal
        try:
            page.select_option('select[id*="tipoComprobante"]', label="RETENCIÓN EN LA FUENTE")
            page.click('button[id*="buscar"]')
            page.wait_for_load_state("networkidle")
            time.sleep(2)
        except Exception as e:
            print(f"Error filtrando retenciones: {e}")
            browser.close()
            return downloaded

        # Iterar filas de resultados y descargar PDFs nuevos
        rows = page.query_selector_all('tr[id*="tabla"]')  # ajustar selector
        for row in rows:
            auth_num = row.query_selector('td:nth-child(2)')  # ajustar columna
            if not auth_num:
                continue
            auth_text = auth_num.inner_text().strip()
            if auth_text in processed_ids:
                continue

            # Clic en botón de descarga PDF de esa fila
            pdf_btn = row.query_selector('a[title*="PDF"]')
            if pdf_btn:
                with context.expect_download() as dl_info:
                    pdf_btn.click()
                download = dl_info.value
                dest = DOWNLOADS_PATH / f"RET_{auth_text}.pdf"
                download.save_as(dest)
                downloaded.append(dest)

        browser.close()

    return downloaded