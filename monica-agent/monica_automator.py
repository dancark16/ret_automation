"""
Automatiza Monica 11 via pywinauto (win32 backend).

PRIMER USO: ejecuta inspect_monica() con Monica abierta para
verificar títulos y nombres de controles exactos.
"""
import time
import re
from pywinauto import Application, keyboard

EXPECTED_RENTA = 2.000
EXPECTED_IVA = 30.000


MONICA_TITLE = "M O N I C A.*"
MODULOS_TITLE = "MODULOS.*"


def inspect_monica():
    app = Application(backend="win32").connect(title_re=MONICA_TITLE, timeout=5)
    for w in app.windows():
        print(f"\nWindow: '{w.window_text()}' | class: '{w.class_name()}'")
        for c in w.children():
            print(f"  [{c.class_name()}] '{c.window_text()}'")


class MonicaAutomator:
    def __init__(self):
        self.app = None

    def connect(self):
        self.app = Application(backend="win32").connect(
            title_re=MONICA_TITLE, timeout=10
        )

    def _win(self, title_re: str, timeout: int = 10):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                # Primero buscar top-level
                wins = self.app.windows(title_re=title_re)
                if wins:
                    return wins[0]
            except Exception:
                pass
            try:
                # Luego buscar entre MDI children de Monica
                main = self.app.window(title_re=MONICA_TITLE)
                for desc in main.descendants():
                    if re.match(title_re, desc.window_text()):
                        return desc
            except Exception:
                pass
            time.sleep(0.3)
        raise TimeoutError(f"Ventana no encontrada: {title_re}")

    def open_facturacion(self):
        main = self._win(MONICA_TITLE)
        main.set_focus()
        time.sleep(0.5)
        keyboard.send_keys("%f")
        time.sleep(1.5)

    def open_invoice(self, invoice_sequential: str) -> bool:
        main = self._win(MONICA_TITLE)
        main.set_focus()
        time.sleep(0.4)
        keyboard.send_keys("%m")   # Alt+M = Modificar
        time.sleep(1)

        # El diálogo de búsqueda puede tener varios títulos posibles
        dlg = None
        for title in ["Modificar Facturas.*", "Buscar.*", ".*[Ff]actura.*[Bb]uscar.*", ".*[Nn]úmero.*"]:
            try:
                dlg = self._win(title, timeout=3)
                break
            except TimeoutError:
                pass

        if dlg is None:
            # Intentar con cualquier ventana nueva que no sea Facturacion ni MODULOS
            time.sleep(0.5)
            known = {"Facturacion", "MODULOS", "MONICA", "M O N I C A   11  - Su Asistente en los Negocios", ""}
            main2 = self.app.window(title_re=MONICA_TITLE)
            for desc in main2.descendants():
                if desc.window_text() not in known:
                    dlg = desc
                    break

        if dlg is None:
            return False

        dlg.set_focus()
        time.sleep(0.2)
        edits = dlg.children(class_name="TEdit")
        if edits:
            edits[0].triple_click_input()
            edits[0].type_keys(invoice_sequential.lstrip("0"), with_spaces=False)
        else:
            keyboard.send_keys(invoice_sequential.lstrip("0"))
        time.sleep(0.3)
        keyboard.send_keys("{ENTER}")
        time.sleep(1.5)

        try:
            self._win(".*[Ff]actura.*", timeout=5)
            return True
        except TimeoutError:
            return False

    def open_retenciones(self):
        inv = self._win(".*[Ff]actura.*|MONICA.*")
        inv.set_focus()
        time.sleep(0.3)
        for ctrl in inv.children():
            if "etenci" in ctrl.window_text():
                ctrl.click_input()
                break
        time.sleep(0.8)

    def check_and_fix_retenciones(self, job: dict) -> dict:
        ret_win = self._win("Retenciones.*")
        ret_win.set_focus()
        time.sleep(0.3)

        result = {"corrected": False, "error": ""}
        edits = ret_win.children(class_name="TEdit")

        if len(edits) < 3:
            result["error"] = f"Se esperaban ≥3 campos TEdit en Retenciones, encontrados: {len(edits)}"
            self._cancel_ret()
            return result

        try:
            renta_actual = float(edits[1].window_text().replace(",", "."))
            iva_actual = float(edits[2].window_text().replace(",", "."))
        except ValueError as e:
            result["error"] = f"No se pudo leer % de Monica: {e}"
            self._cancel_ret()
            return result

        if abs(renta_actual - EXPECTED_RENTA) > 0.001:
            edits[1].triple_click_input()
            edits[1].type_keys(f"{EXPECTED_RENTA:.3f}")
            time.sleep(0.2)
            result["corrected"] = True

        if abs(iva_actual - EXPECTED_IVA) > 0.001:
            edits[2].triple_click_input()
            edits[2].type_keys(f"{EXPECTED_IVA:.3f}")
            time.sleep(0.2)
            result["corrected"] = True

        # Comparar montos con el PDF
        try:
            monto_base = float(edits[0].window_text().replace(",", ""))
            renta_calc = round(monto_base * EXPECTED_RENTA / 100, 2)
            iva_calc = round(monto_base * EXPECTED_IVA / 100, 2)
            pdf_renta = job.get("renta_value", 0)
            pdf_iva = job.get("iva_value", 0)
            if abs(renta_calc - pdf_renta) > 0.05 or abs(iva_calc - pdf_iva) > 0.05:
                result["error"] = (
                    f"Montos no coinciden — PDF: renta={pdf_renta} iva={pdf_iva} | "
                    f"Monica calc: renta={renta_calc} iva={iva_calc}"
                )
                self._cancel_ret()
                return result
        except Exception:
            pass

        for ctrl in ret_win.children():
            if ctrl.window_text().strip().lower() == "aceptar":
                ctrl.click_input()
                break
        time.sleep(0.8)
        return result

    def _cancel_ret(self):
        try:
            w = self._win("Retenciones.*", timeout=3)
            for c in w.children():
                if "ancelar" in c.window_text():
                    c.click_input()
                    break
        except Exception:
            pass

    def set_observaciones(self, ret_serial: str):
        inv = self._win(".*[Ff]actura.*|MONICA.*")
        inv.set_focus()
        time.sleep(0.3)
        obs_text = f"Ret-{ret_serial}"
        try:
            obs = inv.child_window(title_re=".*bservaci.*")
            obs.triple_click_input()
            obs.type_keys(obs_text, with_spaces=True)
        except Exception:
            keyboard.send_keys("{TAB 5}")
            keyboard.send_keys(obs_text)
        time.sleep(0.3)

    def save_and_close_invoice(self):
        inv = self._win(".*[Ff]actura.*|MONICA.*")
        inv.set_focus()
        for ctrl in inv.children():
            if ctrl.window_text().strip().lower() == "aceptar":
                ctrl.click_input()
                return
        keyboard.send_keys("{ENTER}")
        time.sleep(1)

    def close_facturacion(self):
        try:
            w = self._win("Facturacion.*", timeout=3)
            for c in w.children():
                if "alir" in c.window_text():
                    c.click_input()
                    break
        except Exception:
            pass
