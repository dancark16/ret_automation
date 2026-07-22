import re
import pdfplumber
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RetentionData:
    ret_number: str           # "001-002-000001587"
    ret_serial: str           # "000001587"
    client_name: str          # "GUAMBUGUETE SOLORZANO JOSE LUIS"
    invoice_raw: str          # "001002000004200" (del PDF)
    invoice_sequential: str   # "4200"
    invoice_monica: str       # "0000004200" (formato Monica 10 dígitos)
    invoice_date: str         # "17/07/2026"
    renta_pct: float          # 2.00
    renta_base: float         # 708.20
    renta_value: float        # 14.16
    iva_pct: float            # 30.00
    iva_base: float           # 106.23
    iva_value: float          # 31.87
    pdf_path: Path = field(default=None)


def parse_float(s: str) -> float:
    return float(s.replace(",", "").strip())


def extract_retention_data(pdf_path: Path) -> RetentionData:
    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join(
            p.extract_text() for p in pdf.pages if p.extract_text()
        )
        all_tables = []
        for p in pdf.pages:
            tables = p.extract_tables()
            if tables:
                all_tables.extend(tables)

    # --- No. de retención ---
    ret_match = re.search(r'No\.\s+([\d-]+)', full_text)
    ret_number = ret_match.group(1).strip() if ret_match else ""
    ret_serial = ret_number.split("-")[-1]  # "000001587"

    # --- Nombre del cliente (quien emite la retención) ---
    # En el PDF aparece antes de "MAXCOLOR" o similar en el lado izquierdo
    # Buscamos patrón: nombre en mayúsculas seguido de salto de línea
    client_match = re.search(
        r'^([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]+(?:SOLORZANO|AZOGUE|ASSA|GUAM)\s+[A-ZÁÉÍÓÚÑ\s]+)$',
        full_text, re.MULTILINE
    )
    # Fallback: buscar la línea que contiene el nombre del cliente
    if not client_match:
        lines = full_text.splitlines()
        for i, line in enumerate(lines):
            if re.match(r'^[A-ZÁÉÍÓÚÑ ]{10,}$', line.strip()) and len(line.strip()) > 15:
                client_name = line.strip()
                break
        else:
            client_name = "DESCONOCIDO"
    else:
        client_name = client_match.group(1).strip()

    # --- Tabla de comprobantes retenidos ---
    # Buscamos en las tablas la fila con FACTURA
    invoice_raw = ""
    invoice_date = ""
    renta_pct = iva_pct = 0.0
    renta_base = iva_base = 0.0
    renta_value = iva_value = 0.0

    for table in all_tables:
        for row in table:
            if row is None:
                continue
            row_clean = [str(c).strip() if c else "" for c in row]
            row_str = " ".join(row_clean)

            if "FACTURA" in row_str:
                # Extraer número de factura
                for cell in row_clean:
                    cell_no_space = re.sub(r'\s', '', cell)
                    if re.match(r'\d{13,}', cell_no_space):
                        invoice_raw = cell_no_space
                # Fecha emisión
                date_m = re.search(r'\d{2}/\d{2}/\d{4}', row_str)
                if date_m:
                    invoice_date = date_m.group(0)

            # Filas de retención (IVA y Renta)
            if "IVA" in row_str or "Impuesto a la Renta" in row_str or "Renta" in row_str:
                nums = re.findall(r'\d+[\.,]\d+', row_str)
                floats = [parse_float(n) for n in nums]
                if "IVA" in row_str and len(floats) >= 3:
                    iva_base = floats[0]
                    iva_pct = floats[1]
                    iva_value = floats[2]
                elif len(floats) >= 3:
                    renta_base = floats[0]
                    renta_pct = floats[1]
                    renta_value = floats[2]

    # Si la tabla no funcionó, extraer del texto con regex
    if not renta_pct:
        m = re.search(r'(\d+[\.,]\d+)\s+Impuesto a la\s+Renta\s+(\d+[\.,]\d+)\s+(\d+[\.,]\d+)', full_text)
        if m:
            renta_base, renta_pct, renta_value = [parse_float(x) for x in m.groups()]

    if not iva_pct:
        m = re.search(r'(\d+[\.,]\d+)\s+IVA\s+(\d+[\.,]\d+)\s+(\d+[\.,]\d+)', full_text)
        if m:
            iva_base, iva_pct, iva_value = [parse_float(x) for x in m.groups()]

    # --- Número de factura → formato Monica ---
    # "001002000004200" → secuencial = últimos dígitos del tercer bloque
    invoice_sequential = ""
    if invoice_raw:
        # Formato Ecuador: EEEPPP + secuencial (los primeros 6 son establecimiento+punto)
        sequential_raw = invoice_raw[6:]  # "000004200"
        invoice_sequential = str(int(sequential_raw))  # "4200"

    invoice_monica = invoice_sequential.zfill(10)  # "0000004200"

    return RetentionData(
        ret_number=ret_number,
        ret_serial=ret_serial,
        client_name=client_name,
        invoice_raw=invoice_raw,
        invoice_sequential=invoice_sequential,
        invoice_monica=invoice_monica,
        invoice_date=invoice_date,
        renta_pct=renta_pct,
        renta_base=renta_base,
        renta_value=renta_value,
        iva_pct=iva_pct,
        iva_base=iva_base,
        iva_value=iva_value,
        pdf_path=pdf_path,
    )