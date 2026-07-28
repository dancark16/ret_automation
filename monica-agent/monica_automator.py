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
        inv.set_focus()
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
        ret_win.set_focus()
        time.sleep(0.3)
        result = {"corrected": False, "error": ""}

        # Todos los controles son painted — usar coordenadas (diálogo 464x427)
        # Fila 1: Renta % ≈ y=185 (fila IVA estaba en 215, Renta es ~30px más arriba)
        ret_win.click_input(coords=(265, 185))
        time.sleep(0.2)
        keyboard.send_keys("^a")
        keyboard.send_keys(f"{EXPECTED_RENTA:.3f}", with_spaces=False)
        time.sleep(0.3)

        # Fila 2: IVA % ≈ y=215
        ret_win.click_input(coords=(265, 215))
        time.sleep(0.2)
        keyboard.send_keys("^a")
        keyboard.send_keys(f"{EXPECTED_IVA:.3f}", with_spaces=False)
        time.sleep(0.3)

        result["corrected"] = True

        # ACEPTAR ≈ (120, 395)
        ret_win.click_input(coords=(120, 395))
        time.sleep(0.8)
        return result

    def _cancel_ret(self):
        try:
            ret_win = self._win("Retenciones.*", timeout=3)
            # CANCELAR ≈ (375, 395)
            ret_win.click_input(coords=(375, 395))
        except Exception:
            pass

    def set_observaciones(self, ret_serial: str):
        inv = self._win("Facturacion para el Cliente.*")
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
        inv = self._win("Facturacion para el Cliente.*")
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
