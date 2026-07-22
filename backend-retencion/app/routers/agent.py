"""
Endpoints exclusivos para el Monica Agent (PC remota).
Autenticados con X-Agent-Token header.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Retencion
from app.schemas import AgentJobOut, AgentResultIn, ProgressMsg
from app.services.progress import manager
from app.config import settings

router = APIRouter(prefix="/api/agent", tags=["agent"])


def verify_token(x_agent_token: str = Header(...)):
    if x_agent_token != settings.AGENT_TOKEN:
        raise HTTPException(401, "Token inválido")


@router.get("/job", response_model=AgentJobOut | dict)
def obtener_trabajo(db: Session = Depends(get_db), _=Depends(verify_token)):
    r = db.query(Retencion).filter_by(status="en_proceso").first()
    if not r:
        return {"pending": False}
    return {
        "pending": True,
        "id": r.id,
        "ret_number": r.ret_number,
        "ret_serial": r.ret_serial,
        "client_name": r.client_name,
        "invoice_sequential": r.invoice_sequential,
        "invoice_date": r.invoice_date,
        "renta_pct": r.renta_pct,
        "renta_base": r.renta_base,
        "renta_value": r.renta_value,
        "iva_pct": r.iva_pct,
        "iva_base": r.iva_base,
        "iva_value": r.iva_value,
    }


@router.post("/result/{id}")
async def reportar_resultado(
    id: int,
    result: AgentResultIn,
    db: Session = Depends(get_db),
    _=Depends(verify_token),
):
    r = db.get(Retencion, id)
    if not r:
        raise HTTPException(404)

    r.status = "completado" if result.success else "error"
    r.observation = result.observation
    r.processed_at = datetime.utcnow()
    db.commit()

    await manager.broadcast({
        "retencion_id": id,
        "step": "finalizado",
        "status": "ok" if result.success else "error",
        "detail": result.observation,
    })
    return {"ok": True}


@router.post("/progress/{id}")
async def reportar_progreso(
    id: int,
    msg: ProgressMsg,
    _=Depends(verify_token),
):
    await manager.broadcast(msg.model_dump())
    return {"ok": True}
