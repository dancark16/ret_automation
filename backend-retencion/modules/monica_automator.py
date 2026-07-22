"""
Automatiza Monica 11 (app Delphi/Win32) usando pywinauto + teclado.

ANTES DE USAR: ejecuta inspect_monica() una vez con Monica abierta
para verificar los títulos exactos de ventanas y controles.
"""
import time
import pywinauto
from pywinauto import Application, keyboard
from pywinauto.findwindows import ElementNotFoundError
import pyautogui
from config import MONICA_WINDOW_TITLE, EXPECTED_RENTA_PCT, EXPECTED_IVA_PCT, TOLERANCE


def inspect_monica():
    """Corre esto una vez para ver la estructura de ventanas de Monica."""
    app = Application(backend='win32').connect(title_re="MONICA.*|MODULOS.*", timeout=5)
    for w in app.windows():
        print(f"Window: '{w.window_text()}' class='{w.class_name()}'")
        for ctrl in w.children():
            print(f"  Control: '{ctrl.window_text()}' class='{ctrl.class_name()}'")


class MonicaAutomator:
    def __init__(self):
        self.app = None

    def connect(self):
        self.app = Application(backend='win32').connect(
            title_re="MONICA.*|MODULOS.*", timeout=10
        )
        print("Monica conectada.")

    def _wait_window(self, title_re: str, timeout: int = 10):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                wins = self.app.windows(title_re=title_re)
                if wins:
                    return wins[0]
            except Exception:
                pass
            time.sleep(0.3)
        raise TimeoutError(f"Ventana no apareció: {title_re}")

    def open_facturacion(self):
        main = self._wait_window("MODULOS.*")
        main.set_focus()
        time.sleep(0.5)
        # Clic en el botón Facturación (texto visible)
        try:
            btn = main.child_window(title="Facturación", control_type="Button")
            btn.click_input()
        except Exception:
            # Fallback: buscar por texto parcial
            for ctrl in main.children():
                if "acturaci" in ctrl.window_text():
                    ctrl.click_input()
                    break
        time.sleep(1)

    def open_invoice(self, invoice_number: str) -> bool:
        """
        Abre la ventana de Facturación, hace clic en Modificar,
        escribe el número y acepta. Devuelve True si tuvo éxito.
        """
        fact_win = self._wait_window("Facturacion.*")
        fact_win.set_focus()
        time.sleep(0.5)

        # Clic en botón Modificar
        try:
            btn_mod = fact_win.child_window(title="Modificar", control_type="Button")
            btn_mod.click_input()
        except Exception:
            for ctrl in fact_win.children():
                if "odificar" in ctrl.window_text():
                    ctrl.click_input()
                    break
        time.sleep(0.8)

        # Diálogo "Modificar Facturas"
        dlg = self._wait_window("Modificar Facturas.*")
        dlg.set_focus()

        # Escribir número de documento (solo el secuencial numérico)
        edit = dlg.child_window(class_name="TEdit")
        edit.triple_click_input()
        edit.type_keys(invoice_number.lstrip("0"), with_spaces=False)
        time.sleep(0.3)

        # Clic en ACEPTAR
        btn_ok = dlg.child_window(title="ACEPTAR", control_type="Button")
        btn_ok.click_input()
        time.sleep(1.5)

        # Verificar que se abrió la factura
        try:
            self._wait_window(".*Factura.*|.*FACTURA.*", timeout=5)
            return True
        except TimeoutError:
            return False

    def open_retenciones(self):
        """Clic en el botón Retenciones dentro de la factura abierta."""
        inv_win = self._wait_window(".*Factura.*|MONICA.*")
        inv_win.set_focus()
        time.sleep(0.5)
        try:
            btn = inv_win.child_window(title="Retenciones", control_type="Button")
            btn.click_input()
        except Exception:
            for ctrl in inv_win.children():
                if "etenci" in ctrl.window_text():
                    ctrl.click_input()
                    break
        time.sleep(1)

    def check_and_fix_retenciones(self, data) -> dict:
        """
        Lee los % en el diálogo de Retenciones, compara con el PDF,
        corrige si es necesario. Devuelve dict con resultado.
        """
        ret_win = self._wait_window("Retenciones.*")
        ret_win.set_focus()
        time.sleep(0.3)

        result = {"renta_ok": True, "iva_ok": True, "corrected": False, "error": ""}

        # Leer los campos TEdit del diálogo (son los campos de %)
        edits = ret_win.children(class_name="TEdit")
        # En Monica el orden típico es: [Monto Base, Renta%, IVA%] o similar
        # Necesitas verificar con inspect_monica() el orden exacto
        # Por ahora asumimos: edits[1] = Renta%, edits[2] = IVA%
        if len(edits) < 3:
            result["error"] = f"Se esperaban ≥3 campos TEdit, encontrados: {len(edits)}"
            self._cancel_retenciones()
            return result

        try:
            renta_pct_monica = float(edits[1].window_text().replace(",", "."))
            iva_pct_monica = float(edits[2].window_text().replace(",", "."))
        except ValueError:
            result["error"] = "No se pudieron leer los % de Monica"
            self._cancel_retenciones()
            return result

        # Comparar % con lo esperado (2.000 y 30.000)
        renta_ok = abs(renta_pct_monica - EXPECTED_RENTA_PCT) < 0.001
        iva_ok = abs(iva_pct_monica - EXPECTED_IVA_PCT) < 0.001

        result["renta_ok"] = renta_ok
        result["iva_ok"] = iva_ok

        # Comparar montos con el PDF
        # Monica calcula: Monto_Base * % / 100 — si difiere del PDF, hay problema
        try:
            monto_base = float(edits[0].window_text().replace(",", ""))
        except Exception:
            monto_base = 0

        if monto_base > 0:
            renta_calc = round(monto_base * EXPECTED_RENTA_PCT / 100, 2)
            iva_calc = round(monto_base * EXPECTED_IVA_PCT / 100, 2)
            if (abs(renta_calc - data.renta_value) > TOLERANCE or
                    abs(iva_calc - data.iva_value) > TOLERANCE):
                result["error"] = (
                    f"Montos difieren: PDF renta={data.renta_value} calc={renta_calc} | "
                    f"PDF iva={data.iva_value} calc={iva_calc}"
                )

        # Corregir Renta % si es incorrecto
        if not renta_ok:
            edits[1].triple_click_input()
            edits[1].type_keys(f"{EXPECTED_RENTA_PCT:.3f}", with_spaces=False)
            time.sleep(0.3)
            result["corrected"] = True

        # Corregir IVA % si es incorrecto
        if not iva_ok:
            edits[2].triple_click_input()
            edits[2].type_keys(f"{EXPECTED_IVA_PCT:.3f}", with_spaces=False)
            time.sleep(0.3)
            result["corrected"] = True

        # Aceptar retenciones
        btn_ok = ret_win.child_window(title="Aceptar", control_type="Button")
        btn_ok.click_input()
        time.sleep(0.8)

        return result

    def _cancel_retenciones(self):
        try:
            ret_win = self._wait_window("Retenciones.*", timeout=3)
            btn = ret_win.child_window(title="Cancelar", control_type="Button")
            btn.click_input()
        except Exception:
            pass

    def set_observaciones(self, ret_serial: str):
        """Escribe 'Ret-XXXXXX' en el campo Observaciones de la factura."""
        inv_win = self._wait_window(".*Factura.*|MONICA.*")
        inv_win.set_focus()
        time.sleep(0.3)

        obs_text = f"Ret-{ret_serial}"

        # Buscar campo Observaciones por label o posición
        # En Delphi los TEdit tienen un TLabel asociado — buscamos por texto cercano
        try:
            # Intentar encontrar por hint o nombre de control
            obs_edit = inv_win.child_window(title="Observaciones")
            obs_edit.triple_click_input()
            obs_edit.type_keys(obs_text, with_spaces=True)
        except Exception:
            # Fallback: usar Tab para navegar hasta Observaciones
            # Necesitas contar los Tabs desde el foco actual — verificar manualmente
            keyboard.send_keys("{TAB 5}")  # ajustar número de TABs
            keyboard.send_keys(obs_text)
        time.sleep(0.3)

    def save_and_close_invoice(self):
        inv_win = self._wait_window(".*Factura.*|MONICA.*")
        inv_win.set_focus()
        time.sleep(0.3)
        try:
            btn = inv_win.child_window(title="Aceptar", control_type="Button")
            btn.click_input()
        except Exception:
            keyboard.send_keys("{ENTER}")
        time.sleep(1)

    def close_facturacion(self):
        try:
            fact_win = self._wait_window("Facturacion.*", timeout=3)
            fact_win.child_window(title="Salir", control_type="Button").click_input()
        except Exception:
            pass