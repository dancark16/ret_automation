from pathlib import Path
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

HEADERS = ["FECHA", "CLIENTE", "FACTURA", "No. RETENCIÓN", "RENTA %", "IVA %", "TOTAL RET.", "OBSERVACIÓN"]
YELLOW = PatternFill("solid", fgColor="FFFF00")

MONTHS_ES = {
    1:"ene", 2:"feb", 3:"mar", 4:"abr", 5:"may", 6:"jun",
    7:"jul", 8:"ago", 9:"sep", 10:"oct", 11:"nov", 12:"dic"
}


def register_retention(path: Path, job: dict, invoice_date: str, observation: str = ""):
    if path.exists():
        wb = openpyxl.load_workbook(path)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Retenciones"
        for col, h in enumerate(HEADERS, 1):
            c = ws.cell(row=1, column=col, value=h)
            c.font = Font(bold=True)
        ws.column_dimensions["A"].width = 10
        ws.column_dimensions["B"].width = 35
        ws.column_dimensions["H"].width = 40

    try:
        fecha = datetime.strptime(invoice_date, "%d/%m/%Y")
        fecha_str = f"{fecha.day}-{MONTHS_ES[fecha.month]}"
    except Exception:
        fecha_str = invoice_date

    total_ret = round(job.get("renta_value", 0) + job.get("iva_value", 0), 2)

    row = [
        fecha_str,
        job.get("client_name", ""),
        job.get("invoice_sequential", ""),
        job.get("ret_number", ""),
        job.get("renta_pct", 0),
        job.get("iva_pct", 0),
        total_ret,
        observation,
    ]

    next_row = ws.max_row + 1
    for col, val in enumerate(row, 1):
        cell = ws.cell(row=next_row, column=col, value=val)
        cell.alignment = Alignment(horizontal="left")
        if observation and col == len(HEADERS):
            cell.fill = YELLOW

    wb.save(path)
