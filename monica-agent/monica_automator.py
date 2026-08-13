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
        import ctypes
        # Permite que este proceso tome el foco de ventanas en Windows
        ctypes.windll.user32.AllowSetForegroundWindow(-1)
        self.app = Application(backend="win32").connect(
            title_re=MONICA_TITLE, timeout=10
        )

    def _focus(self, win):
        """set_focus tolerante — ignora el error de SetForegroundWindow."""
        try:
            win.set_focus()
        except Exception:
            pass

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

    def click_comenzar(self):
        """Desde la pantalla de inicio de Monica: Comenzar → Seleccionar Empresa."""
        import pyautogui
        pyautogui.FAILSAFE = False
        main = self._win(MONICA_TITLE)
        r = main.rectangle()
        # "Comenzar" offset verificado: (1161, 446)
        pyautogui.click(r.left + 1161, r.top + 446)
        time.sleep(1.0)
        # Dialogo "Lista de Empresas" — empresa ya seleccionada, Enter = Seleccionar Empresa
        try:
            dlg = self._win("Lista de Empresas.*", timeout=4)
            self._focus(dlg)
            time.sleep(0.3)
            keyboard.send_keys("{ENTER}")
            time.sleep(2.0)
        except TimeoutError:
            pass  # Ya estaba en MODULOS, no apareció el diálogo

    def open_facturacion(self):
        import pyautogui
        pyautogui.FAILSAFE = False
        main = self._win(MONICA_TITLE)
        r = main.rectangle()
        # Click directo en botón Facturación — offset verificado (205, 240)
        pyautogui.click(r.left + 205, r.top + 240)
        time.sleep(2.0)
        # Verificar que Facturación abrió
        try:
            self._win("Facturacion.*", timeout=4)
        except TimeoutError:
            raise Exception("No se pudo abrir el módulo de Facturación")

    def open_invoice(self, invoice_sequential: str) -> bool:
        import pyautogui
        pyautogui.FAILSAFE = False
        # Click en botón Modificar de la ventana Facturación
        fac = self._win("Facturacion.*")
        rf = fac.rectangle()
        # Botón Modificar verificado anteriormente con Alt+M — ahora click directo
        pyautogui.click(rf.left + 155, rf.top + 625)
        time.sleep(1)

        # Buscar el diálogo "Modificar Facturas"
        dlg = None
        deadline = time.time() + 8
        while time.time() < deadline:
            known = {"Facturacion", "MODULOS", "MONICA", ""}
            main2 = self.app.window(title_re=MONICA_TITLE)
            for desc in main2.descendants():
                if desc.window_text() not in known and desc.window_text() != main2.window_text():
                    dlg = desc
                    break
            if dlg:
                break
            time.sleep(0.3)

        if dlg is None:
            return False

        dlg.set_focus()
        time.sleep(0.3)
        # El campo Nro. Documento ya está enfocado al abrir el diálogo
        keyboard.send_keys("^a")
        time.sleep(0.1)
        keyboard.send_keys(invoice_sequential.lstrip("0"), with_spaces=False)
        time.sleep(0.2)
        # Tab hasta ACEPTAR y Enter
        keyboard.send_keys("{TAB}{SPACE}")
        time.sleep(2)

        try:
            self._win("Facturacion para el Cliente.*", timeout=6)
            return True
        except TimeoutError:
            return False

    def open_retenciones(self):
        inv = self._win("Facturacion para el Cliente.*")
        self._focus(inv)
        time.sleep(0.3)
        # Botón "Retenciones" es painted — click por coordenadas relativas a la ventana
        rect = inv.rectangle()
        w = rect.right - rect.left
        h = rect.bottom - rect.top
        # Botón "Retenciones" — sidebar derecho, último botón
        bx = int(w * 0.947)   # ~895px en ventana de 943px
        by = int(h * 0.916)   # ~638px en ventana de 697px
        inv.click_input(coords=(bx, by))
        time.sleep(0.8)

    def check_and_fix_retenciones(self, job: dict) -> dict:
        ret_win = self._win("Retenciones.*")
        self._focus(ret_win)
        time.sleep(0.3)
        result = {"corrected": False, "error": ""}

        renta_pct = float(job.get("renta_pct", EXPECTED_RENTA))
        iva_pct = float(job.get("iva_pct", EXPECTED_IVA))

        # Fila 1: Renta % ≈ (265, 185)
        ret_win.click_input(coords=(265, 185))
        time.sleep(0.2)
        keyboard.send_keys("^a")
        keyboard.send_keys(f"{renta_pct:.3f}", with_spaces=False)
        time.sleep(0.3)

        # Fila 2: IVA % ≈ (265, 215)
        ret_win.click_input(coords=(265, 215))
        time.sleep(0.2)
        keyboard.send_keys("^a")
        keyboard.send_keys(f"{iva_pct:.3f}", with_spaces=False)
        time.sleep(0.3)

        result["corrected"] = True

        # ACEPTAR ≈ (120, 395)
        ret_win.click_input(coords=(120, 395))
        time.sleep(0.8)
        return result

    def is_on_home_screen(self) -> bool:
        """Retorna True si Monica está en la pantalla de inicio (sin MODULOS abierto)."""
        try:
            main = self.app.window(title_re=MONICA_TITLE)
            for desc in main.descendants():
                try:
                    if re.match(MODULOS_TITLE, desc.window_text()):
                        return False
                except Exception:
                    continue
            return True
        except Exception:
            return True  # Si hay error asumimos home screen e intentamos navegar

    def _cancel_ret(self):
        try:
            ret_win = self._win("Retenciones.*", timeout=3)
            # CANCELAR ≈ (375, 395)
            ret_win.click_input(coords=(375, 395))
        except Exception:
            pass

    def set_observaciones(self, ret_serial: str):
        inv = self._win("Facturacion para el Cliente.*")
        self._focus(inv)
        time.sleep(0.3)
        obs_text = f"Ret-{ret_serial}"
        # Campo Observaciones — ventana 943x697, campo inferior izquierdo ≈ (210, 470)
        inv.click_input(coords=(210, 470))
        time.sleep(0.2)
        keyboard.send_keys("^a")
        keyboard.send_keys(obs_text, with_spaces=True)
        time.sleep(0.3)

    def save_and_close_invoice(self):
        import pyautogui
        pyautogui.FAILSAFE = False
        inv = self._win("Facturacion para el Cliente.*")
        self._focus(inv)
        time.sleep(0.3)

        r = inv.rectangle()
        # "Imprimir Documento" checkbox — client offset verificado: (41, 595)
        pyautogui.click(r.left + 41, r.top + 595)
        time.sleep(0.3)
        # Botón ACEPTAR
        pyautogui.click(r.left + 205, r.top + 655)
        time.sleep(1.5)

        # Modal "Modificar documento. Confirmar ¿ Si / No ?"
        try:
            confirm = self._win("Modificar documento.*", timeout=4)
            cr = confirm.rectangle()
            time.sleep(0.2)
            # Botón "Sí" — offset verificado: (105, 165)
            pyautogui.click(cr.left + 105, cr.top + 165)
            time.sleep(1)
        except TimeoutError:
            pass

    def close_facturacion(self):
        try:
            w = self._win("Facturacion.*", timeout=3)
            self._focus(w)
            time.sleep(0.3)
            keyboard.send_keys("%s")  # Alt+S = Salir
            time.sleep(1.0)
        except Exception:
            pass
