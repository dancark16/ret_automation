from datetime import datetime
from pydantic import BaseModel


class RetenciónBase(BaseModel):
    ret_number: str
    ret_serial: str
    client_name: str
    invoice_sequential: str
    invoice_date: str
    renta_pct: float
    renta_base: float
    renta_value: float
    iva_pct: float
    iva_base: float
    iva_value: float


class RetenciónOut(RetenciónBase):
    id: int
    status: str
    observation: str
    created_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}


class AgentJobOut(RetenciónBase):
    id: int
    pending: bool = True


class AgentResultIn(BaseModel):
    success: bool
    observation: str = ""


class ProgressMsg(BaseModel):
    retencion_id: int
    step: str
    status: str   # running | ok | error
    detail: str = ""
