"""
Orquestador principal del flujo de retenciones.
Uso: python main.py
"""
import json
import sys
from pathlib import Path
from config import DOWNLOADS_PATH, PDF_STORAGE_BASE, EXCEL_PATH

from modules.pdf_extractor import extract_retention_data
from modules.excel_manager import register_retention
from modules.file_manager import save_retention_pdf
from modules.monica_automator import MonicaAutomator
from modules.sri_downloader import download_new_retentions

PROCESSED_FILE = Path("processed_ids.json")


def load_processed() -> set:
    if PROCESSED_FILE.exists():
        return set(json.loads(PROCESSED_FILE.read_text()))
    return set()


def save_processed(ids: set):
    PROCESSED_FILE.write_text(json.dumps(list(ids)))


def process_pdf(pdf_path: Path, monica: MonicaAutomator, processed_ids: set):
    print(f"\n{'='*60}")
    print(f"Procesando: {pdf_path.name}")

    # 1. Extraer datos del PDF
    data = extract_retention_data(pdf_path)
    print(f"  Cliente: {data.client_name}")
    print(f"  Factura Monica: {data.invoice_monica}  |  Ret: {data.ret_number}")
    print(f"  Renta: {data.renta_pct}% = {data.renta_value}  |  IVA: {data.iva_pct}% = {data.iva_value}")

    # 2. Abrir Monica y procesar
    observation = ""
    monica_ok = False
    try:
        monica.open_facturacion()
        opened = monica.open_invoice(data.invoice_sequential)

        if not opened:
            observation = f"Factura {data.invoice_sequential} no encontrada en Monica"
            print(f"  ⚠ {observation}")
        else:
            monica.open_retenciones()
            ret_result = monica.check_and_fix_retenciones(data)

            if ret_result["error"]:
                observation = ret_result["error"]
                print(f"  ⚠ Error retenciones: {observation}")
                monica.close_facturacion()
            else:
                if ret_result["corrected"]:
                    print(f"  ✓ Porcentajes corregidos")
                monica.set_observaciones(data.ret_serial)
                monica.save_and_close_invoice()
                monica.close_facturacion()
                monica_ok = True
                print(f"  ✓ Monica actualizada. Observaciones: Ret-{data.ret_serial}")

    except Exception as e:
        observation = f"Error Monica: {e}"
        print(f"  ✗ {observation}")
        try:
            monica.close_facturacion()
        except Exception:
            pass

    # 3. Registrar en Excel
    register_retention(EXCEL_PATH, data, data.invoice_date, observation)
    print(f"  ✓ Registrado en Excel")

    # 4. Renombrar y guardar PDF
    saved_path = save_retention_pdf(pdf_path, data, data.invoice_date, PDF_STORAGE_BASE)
    print(f"  ✓ PDF guardado: {saved_path.name}")

    # 5. Marcar como procesado
    processed_ids.add(data.ret_number)
    save_processed(processed_ids)


def main():
    processed_ids = load_processed()

    # Paso 1: Descargar del SRI (o usar PDFs ya descargados en DOWNLOADS_PATH)
    if "--skip-download" in sys.argv:
        # Modo manual: procesar PDFs que ya están en Downloads
        pdfs = list(DOWNLOADS_PATH.glob("Comprobante de Retención*.pdf"))
        pdfs += list(DOWNLOADS_PATH.glob("RET_*.pdf"))
    else:
        print("Descargando retenciones del SRI...")
        pdfs = download_new_retentions(processed_ids)

    if not pdfs:
        print("No hay retenciones nuevas para procesar.")
        return

    print(f"\nSe procesarán {len(pdfs)} retención(es).")

    # Paso 2: Conectar a Monica
    monica = MonicaAutomator()
    monica.connect()

    # Paso 3: Procesar cada PDF
    for pdf_path in pdfs:
        data = extract_retention_data(pdf_path)
        if data.ret_number in processed_ids:
            print(f"Ya procesada: {data.ret_number}")
            continue
        process_pdf(pdf_path, monica, processed_ids)

    print("\n✓ Proceso completado.")


if __name__ == "__main__":
    main()