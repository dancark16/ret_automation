import time
from pathlib import Path
from datetime import datetime
import openpyxl
from openpyxl.styles import PatternFill, Alignment, Font

YELLOW = PatternFill("solid", fgColor="FFFF00")
HEADERS = ["FECHA", "CLIENTE", "FACTURA", "No. RETENCIÓN", "RENTA %", "IVA %", "TOTAL RET.", "OBSERVACIÓN"]

MONTHS_ES = {
    1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
    7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic"
}


def _create_workbook(path: Path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "RETENCIONES"
    for col, h in enumerate(HEADERS, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="003DA5")
        cell.font = Font(bold=True, color="FFFFFF")
    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 30
    ws.column_dimensions["C"].width = 10
    ws.column_dimensions["D"].width = 22
    ws.column_dimensions["E"].width = 10
    ws.column_dimensions["F"].width = 10
    ws.column_dimensions["G"].width = 12
    ws.column_dimensions["H"].width = 40
    wb.save(path)


def _next_empty_row(ws) -> int:
    row = 2
    while ws.cell(row=row, column=1).value is not None:
        row += 1
    return row


def register_retention(path: Path, job: dict, invoice_date: str, observation: str = ""):
    if not path.exists():
        _create_workbook(path)

    wb = openpyxl.load_workbook(path)
    ws = wb["RETENCIONES"] if "RETENCIONES" in wb.sheetnames else wb.active

    try:
        fecha = datetime.strptime(invoice_date, "%d/%m/%Y")
        fecha_str = f"{fecha.day}-{MONTHS_ES[fecha.month]}"
    except Exception:
        fecha_str = invoice_date

    from client_aliases import resolve_client
    total_ret = round(job.get("renta_value", 0) + job.get("iva_value", 0), 2)

    row_data = [
        fecha_str,
        resolve_client(job.get("client_name", "")),
        job.get("invoice_sequential", ""),
        job.get("ret_number", ""),
        job.get("renta_pct", 0),
        job.get("iva_pct", 0),
        total_ret,
        observation,
    ]

    next_row = _next_empty_row(ws)
    for col, val in enumerate(row_data, 1):
        cell = ws.cell(row=next_row, column=col, value=val)
        cell.alignment = Alignment(horizontal="left")

    if observation:
        for col in range(1, len(row_data) + 1):
            ws.cell(row=next_row, column=col).fill = YELLOW

    for attempt in range(5):
        try:
            wb.save(path)
            return
        except PermissionError:
            if attempt < 4:
                print(f"[EXCEL] Archivo bloqueado, ciérralo... reintentando en 5s ({attempt+1}/5)")
                time.sleep(5)
            else:
                raise
