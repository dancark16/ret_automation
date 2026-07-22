from datetime import datetime
from sqlalchemy import Integer, String, Float, LargeBinary, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Retencion(Base):
    __tablename__ = "retenciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ret_number: Mapped[str] = mapped_column(String, unique=True, index=True)
    ret_serial: Mapped[str] = mapped_column(String)
    client_name: Mapped[str] = mapped_column(String)
    invoice_sequential: Mapped[str] = mapped_column(String)
    invoice_date: Mapped[str] = mapped_column(String)

    renta_pct: Mapped[float] = mapped_column(Float, default=0)
    renta_base: Mapped[float] = mapped_column(Float, default=0)
    renta_value: Mapped[float] = mapped_column(Float, default=0)
    iva_pct: Mapped[float] = mapped_column(Float, default=0)
    iva_base: Mapped[float] = mapped_column(Float, default=0)
    iva_value: Mapped[float] = mapped_column(Float, default=0)

    # pendiente | en_proceso | completado | error
    status: Mapped[str] = mapped_column(String, default="pendiente")
    observation: Mapped[str] = mapped_column(String, default="")

    pdf_bytes: Mapped[bytes] = mapped_column(LargeBinary)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
