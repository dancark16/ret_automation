"""
Monica Agent — corre en el PC donde está instalado Monica 11.
Hace polling al backend, ejecuta la automatización y reporta resultados.

Uso: python agent.py
"""
import time
import os
import requests
from dotenv import load_dotenv
from monica_automator import MonicaAutomator
from excel_manager import register_retention
from file_manager import save_retention_pdf
from pathlib import Path

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
TOKEN = os.getenv("AGENT_TOKEN", "")
EXCEL_PATH = Path(os.getenv("EXCEL_PATH", "retenciones.xlsx"))
PDF_STORAGE = Path(os.getenv("PDF_STORAGE", "."))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "5"))

HEADERS = {"X-Agent-Token": TOKEN}


def progress(retencion_id: int, step: str, status: str, detail: str = ""):
    try:
        requests.post(
            f"{API_URL}/api/agent/progress/{retencion_id}",
            json={"retencion_id": retencion_id, "step": step, "status": status, "detail": detail},
            headers=HEADERS,
            timeout=5,
        )
    except Exception:
        pass


def report_result(retencion_id: int, success: bool, observation: str = ""):
    requests.post(
        f"{API_URL}/api/agent/result/{retencion_id}",
        json={"success": success, "observation": observation},
        headers=HEADERS,
        timeout=10,
    )


def process_job(job: dict, monica: MonicaAutomator):
    rid = job["id"]
    observation = ""
    success = False

    try:
        # Paso 1: Abrir facturación — click_comenzar es seguro desde cualquier pantalla
        progress(rid, "monica_facturacion", "running", "Abriendo módulo de facturación...")
        monica.click_comenzar()
        monica.open_facturacion()
        progress(rid, "monica_facturacion", "ok")

        # Paso 2: Abrir factura
        progress(rid, "monica_factura", "running", f"Buscando factura {job['invoice_sequential']}...")
        opened = monica.open_invoice(job["invoice_sequential"])
        if not opened:
            raise Exception(f"Factura {job['invoice_sequential']} no encontrada en Monica")
        progress(rid, "monica_factura", "ok")

        # Paso 3: Retenciones
        progress(rid, "monica_retenciones", "running", "Verificando retenciones...")
        monica.open_retenciones()
        ret_result = monica.check_and_fix_retenciones(job)

        if ret_result.get("error"):
            observation = ret_result["error"]
            progress(rid, "monica_retenciones", "error", observation)
            monica.close_facturacion()
        else:
            if ret_result.get("corrected"):
                progress(rid, "monica_retenciones", "ok", "Porcentajes corregidos")
            else:
                progress(rid, "monica_retenciones", "ok", "Porcentajes correctos")

            # Paso 4: Observaciones
            progress(rid, "monica_obs", "running", f"Escribiendo Ret-{job['ret_serial']}...")
            monica.set_observaciones(job["ret_serial"])
            monica.save_and_close_invoice()
            monica.close_facturacion()
            progress(rid, "monica_obs", "ok")
            success = True

        # Paso 5: Descargar PDF del backend y guardar localmente
        progress(rid, "pdf", "running", "Guardando PDF...")
        pdf_resp = requests.get(f"{API_URL}/api/retenciones/{rid}/pdf", headers=HEADERS, timeout=15)
        if pdf_resp.ok:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf_resp.content)
                tmp_path = Path(tmp.name)
            saved = save_retention_pdf(tmp_path, job, job["invoice_date"], PDF_STORAGE)
            tmp_path.unlink(missing_ok=True)
            progress(rid, "pdf", "ok", f"Guardado: {saved.name}")
        else:
            progress(rid, "pdf", "error", "No se pudo descargar el PDF del servidor")

        # Paso 6: Excel
        progress(rid, "excel", "running", "Registrando en Excel...")
        register_retention(EXCEL_PATH, job, job["invoice_date"], observation)
        progress(rid, "excel", "ok")

    except Exception as e:
        observation = str(e)
        print(f"[ERROR] {observation}")
        progress(rid, "error_general", "error", observation)
        try:
            monica.close_facturacion()
        except Exception:
            pass

    report_result(rid, success, observation)
    if success:
        print(f"[OK] Ret {job['ret_number']} procesada correctamente")
    else:
        print(f"[FALLO] Ret {job['ret_number']} — {observation}")


def main():
    print(f"Monica Agent iniciado. Conectando a {API_URL} ...")
    monica = MonicaAutomator()

    try:
        monica.connect()
        print("Monica 11 conectada.")
        if monica.is_on_home_screen():
            print("Pantalla de inicio detectada, haciendo click en Comenzar...")
            monica.click_comenzar()
    except Exception as e:
        print(f"No se pudo conectar a Monica 11: {e}")
        print("Asegúrate de que Monica 11 esté abierta antes de iniciar el agente.")
        return

    print(f"Polling cada {POLL_INTERVAL}s. Esperando trabajos...\n")

    while True:
        try:
            r = requests.get(f"{API_URL}/api/agent/job", headers=HEADERS, timeout=10)
            job = r.json()

            if job.get("pending"):
                print(f"[JOB] Ret {job['ret_number']} | Factura {job['invoice_sequential']} | {job['client_name']}")
                process_job(job, monica)
                print(f"[DONE] Ret {job['ret_number']}\n")
            else:
                time.sleep(POLL_INTERVAL)

        except requests.exceptions.ConnectionError:
            print(f"Sin conexión al backend ({API_URL}), reintentando en 15s...")
            time.sleep(15)
        except KeyboardInterrupt:
            print("\nAgente detenido.")
            break
        except Exception as e:
            print(f"Error inesperado: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
