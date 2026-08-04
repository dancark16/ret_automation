from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Retencion
from app.schemas import RetenciónOut
from app.services.pdf_extractor import extract_from_bytes
from app.services.progress import manager

router = APIRouter(prefix="/api/retenciones", tags=["retenciones"])


@router.get("", response_model=list[RetenciónOut])
def listar(db: Session = Depends(get_db)):
    return db.query(Retencion).order_by(Retencion.created_at.desc()).all()


@router.get("/{id}", response_model=RetenciónOut)
def detalle(id: int, db: Session = Depends(get_db)):
    r = db.get(Retencion, id)
    if not r:
        raise HTTPException(404, "No encontrada")
    return r


@router.get("/{id}/pdf")
def descargar_pdf(id: int, db: Session = Depends(get_db)):
    r = db.get(Retencion, id)
    if not r:
        raise HTTPException(404, "No encontrada")
    return Response(
        content=r.pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="RET_{r.ret_number}.pdf"'},
    )


@router.post("/upload", response_model=RetenciónOut, status_code=201)
async def subir_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    pdf_bytes = await file.read()
    try:
        data = extract_from_bytes(pdf_bytes)
    except Exception as e:
        raise HTTPException(422, f"No se pudo leer el PDF: {e}")

    existente = db.query(Retencion).filter_by(ret_number=data.ret_number).first()
    if existente:
        raise HTTPException(409, f"Retención {data.ret_number} ya registrada")

    r = Retencion(
        ret_number=data.ret_number,
        ret_serial=data.ret_serial,
        client_name=data.client_name,
        invoice_sequential=data.invoice_sequential,
        invoice_date=data.invoice_date,
        renta_pct=data.renta_pct,
        renta_base=data.renta_base,
        renta_value=data.renta_value,
        iva_pct=data.iva_pct,
        iva_base=data.iva_base,
        iva_value=data.iva_value,
        pdf_bytes=pdf_bytes,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


@router.delete("/{id}", status_code=204)
def eliminar(id: int, db: Session = Depends(get_db)):
    r = db.get(Retencion, id)
    if not r:
        raise HTTPException(404, "No encontrada")
    db.delete(r)
    db.commit()


@router.post("/{id}/reset", response_model=RetenciónOut)
def reset_status(id: int, db: Session = Depends(get_db)):
    r = db.get(Retencion, id)
    if not r:
        raise HTTPException(404, "No encontrada")
    r.status = "pendiente"
    r.observation = ""
    r.processed_at = None
    db.commit()
    db.refresh(r)
    return r


@router.post("/{id}/procesar", response_model=RetenciónOut)
async def encolar_procesamiento(id: int, db: Session = Depends(get_db)):
    r = db.get(Retencion, id)
    if not r:
        raise HTTPException(404, "No encontrada")
    if r.status not in ("pendiente", "error"):
        raise HTTPException(400, f"No se puede procesar una retención en estado '{r.status}'")

    r.status = "en_proceso"
    db.commit()
    db.refresh(r)

    await manager.broadcast({
        "retencion_id": r.id,
        "step": "encolado",
        "status": "running",
        "detail": "Esperando al agente Monica...",
    })
    return r
