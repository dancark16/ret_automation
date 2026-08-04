from pathlib import Path
from datetime import datetime
import openpyxl
from openpyxl.styles import PatternFill, Alignment

YELLOW = PatternFill("solid", fgColor="FFFF00")
SHEET_NAME = "RETENCIONES"
HEADER_ROW = 3   # Los headers están en la fila 3
DATA_START = 4   # Los datos empiezan en la fila 4

MONTHS_ES = {
    1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
    7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic"
}


def _next_empty_row(ws) -> int:
    """Encuentra la primera fila vacía en columna A a partir de DATA_START."""
    row = DATA_START
    while ws.cell(row=row, column=1).value is not None:
        row += 1
    return row


def register_retention(path: Path, job: dict, invoice_date: str, observation: str = ""):
    if not path.exists():
        raise FileNotFoundError(f"Excel no encontrado: {path}")

    wb = openpyxl.load_workbook(path)

    # Usar la hoja RETENCIONES (3ra hoja)
    if SHEET_NAME in wb.sheetnames:
        ws = wb[SHEET_NAME]
    else:
        ws = wb.worksheets[2]

    try:
        fecha = datetime.strptime(invoice_date, "%d/%m/%Y")
        fecha_str = f"{fecha.day}-{MONTHS_ES[fecha.month]}"
    except Exception:
        fecha_str = invoice_date

    total_ret = round(job.get("renta_value", 0) + job.get("iva_value", 0), 2)

    row_data = [
        fecha_str,                          # A - FECHA
        job.get("client_name", ""),         # B - CLIENTE
        job.get("invoice_sequential", ""),  # C - FACTURA
        job.get("ret_number", ""),          # D - No. RETENCIÓN
        job.get("renta_pct", 0),            # E - RENTA %
        job.get("iva_pct", 0),              # F - IVA %
        total_ret,                          # G - TOTAL RET.
        observation,                        # H - OBSERVACIÓN
    ]

    next_row = _next_empty_row(ws)
    for col, val in enumerate(row_data, 1):
        cell = ws.cell(row=next_row, column=col, value=val)
        cell.alignment = Alignment(horizontal="left")

    # Fila amarilla si hay observación (indica corrección manual)
    if observation:
        for col in range(1, len(row_data) + 1):
            ws.cell(row=next_row, column=col).fill = YELLOW

    wb.save(path)
