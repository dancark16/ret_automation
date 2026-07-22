import io
import re
import pdfplumber
from dataclasses import dataclass


@dataclass
class RetentionData:
    ret_number: str
    ret_serial: str
    client_name: str
    invoice_raw: str
    invoice_sequential: str
    invoice_date: str
    renta_pct: float
    renta_base: float
    renta_value: float
    iva_pct: float
    iva_base: float
    iva_value: float


def _parse_float(s: str) -> float:
    return float(s.replace(",", "").strip())


def extract_from_bytes(pdf_bytes: bytes) -> RetentionData:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        full_text = "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())
        all_tables = []
        for p in pdf.pages:
            tables = p.extract_tables()
            if tables:
                all_tables.extend(tables)

    # No. retención
    ret_match = re.search(r'No\.\s+([\d-]+)', full_text)
    ret_number = ret_match.group(1).strip() if ret_match else ""
    ret_serial = ret_number.split("-")[-1]

    # Nombre del cliente — línea en mayúsculas de 15+ caracteres, no es dirección ni dato genérico
    skip_words = {"HUACHI", "PANAMERICANA", "CEVALLOS", "AMBIENTE", "EMISIÓN", "PRODUCCIÓN"}
    client_name = "DESCONOCIDO"
    for line in full_text.splitlines():
        clean = line.strip()
        if (
            re.match(r'^[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{14,}$', clean)
            and not any(w in clean for w in skip_words)
        ):
            client_name = clean
            break

    # Tabla de comprobantes retenidos
    invoice_raw = invoice_date = ""
    renta_pct = iva_pct = renta_base = iva_base = renta_value = iva_value = 0.0

    for table in all_tables:
        for row in table:
            if not row:
                continue
            cells = [str(c).strip() if c else "" for c in row]
            row_str = " ".join(cells)

            if "FACTURA" in row_str:
                for cell in cells:
                    no_space = re.sub(r'\s', '', cell)
                    if re.match(r'^\d{13,}$', no_space):
                        invoice_raw = no_space
                date_m = re.search(r'\d{2}/\d{2}/\d{4}', row_str)
                if date_m:
                    invoice_date = date_m.group(0)

            if "IVA" in row_str or "Renta" in row_str:
                nums = re.findall(r'\d+[.,]\d+', row_str)
                floats = [_parse_float(n) for n in nums]
                if "IVA" in row_str and len(floats) >= 3:
                    iva_base, iva_pct, iva_value = floats[0], floats[1], floats[2]
                elif len(floats) >= 3:
                    renta_base, renta_pct, renta_value = floats[0], floats[1], floats[2]

    # Fallback regex si las tablas fallaron
    if not renta_pct:
        m = re.search(r'([\d.,]+)\s+Impuesto a la\s+Renta\s+([\d.,]+)\s+([\d.,]+)', full_text)
        if m:
            renta_base, renta_pct, renta_value = [_parse_float(x) for x in m.groups()]

    if not iva_pct:
        m = re.search(r'([\d.,]+)\s+IVA\s+([\d.,]+)\s+([\d.,]+)', full_text)
        if m:
            iva_base, iva_pct, iva_value = [_parse_float(x) for x in m.groups()]

    # Número de factura → secuencial Monica
    invoice_sequential = ""
    if invoice_raw:
        sequential_raw = invoice_raw[6:]
        invoice_sequential = str(int(sequential_raw))

    return RetentionData(
        ret_number=ret_number,
        ret_serial=ret_serial,
        client_name=client_name,
        invoice_raw=invoice_raw,
        invoice_sequential=invoice_sequential,
        invoice_date=invoice_date,
        renta_pct=renta_pct,
        renta_base=renta_base,
        renta_value=renta_value,
        iva_pct=iva_pct,
        iva_base=iva_base,
        iva_value=iva_value,
    )
