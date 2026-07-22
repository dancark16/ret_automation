from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import retenciones, sri, agent, ws

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Retenciones API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(retenciones.router)
app.include_router(sri.router)
app.include_router(agent.router)
app.include_router(ws.router)


@app.get("/health")
def health():
    return {"status": "ok"}
