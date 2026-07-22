import re
import shutil
from pathlib import Path
from datetime import datetime


def _sanitize(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '', name).strip()


def get_next_sequence(base_path: Path, day: int) -> int:
    pattern = re.compile(rf'^RET {day}\.(\d+)', re.IGNORECASE)
    existing = [int(m.group(1)) for f in base_path.glob(f"RET {day}.*") if (m := pattern.match(f.name))]
    return max(existing, default=0) + 1


def save_retention_pdf(
    source_pdf: Path,
    data,
    invoice_date: str,
    base_storage: Path,
) -> Path:
    # Carpeta destino: base/YYYY/MES
    fecha = datetime.strptime(invoice_date, "%d/%m/%Y")
    month_names = {
        1:"ENERO", 2:"FEBRERO", 3:"MARZO", 4:"ABRIL",
        5:"MAYO", 6:"JUNIO", 7:"JULIO", 8:"AGOSTO",
        9:"SEPTIEMBRE", 10:"OCTUBRE", 11:"NOVIEMBRE", 12:"DICIEMBRE"
    }
    dest_folder = base_storage / str(fecha.year) / month_names[fecha.month]
    dest_folder.mkdir(parents=True, exist_ok=True)

    day = fecha.day
    seq = get_next_sequence(dest_folder, day)
    client_short = _sanitize(data.client_name)[:25]
    invoice_num = data.invoice_sequential

    filename = f"RET {day}.{seq} {client_short} F.{invoice_num}.pdf"
    dest_path = dest_folder / filename

    shutil.copy2(source_pdf, dest_path)
    return dest_path