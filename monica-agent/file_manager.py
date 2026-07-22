import re
import shutil
from pathlib import Path
from datetime import datetime

MONTHS_ES = {
    1:"ENERO", 2:"FEBRERO", 3:"MARZO", 4:"ABRIL", 5:"MAYO", 6:"JUNIO",
    7:"JULIO", 8:"AGOSTO", 9:"SEPTIEMBRE", 10:"OCTUBRE", 11:"NOVIEMBRE", 12:"DICIEMBRE"
}


def _sanitize(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '', name).strip()


def get_next_sequence(folder: Path, day: int) -> int:
    pattern = re.compile(rf'^RET {day}\.(\d+)', re.IGNORECASE)
    nums = [int(m.group(1)) for f in folder.iterdir() if f.is_file() and (m := pattern.match(f.name))]
    return max(nums, default=0) + 1


def save_retention_pdf(source: Path, job: dict, invoice_date: str, base: Path) -> Path:
    try:
        fecha = datetime.strptime(invoice_date, "%d/%m/%Y")
    except Exception:
        fecha = datetime.today()

    folder = base / str(fecha.year) / MONTHS_ES[fecha.month]
    folder.mkdir(parents=True, exist_ok=True)

    day = fecha.day
    seq = get_next_sequence(folder, day)
    client = _sanitize(job.get("client_name", "CLIENTE"))[:25]
    inv = job.get("invoice_sequential", "0")

    filename = f"RET {day}.{seq} {client} F.{inv}.pdf"
    dest = folder / filename
    shutil.copy2(source, dest)
    return dest
