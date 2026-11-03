from fastapi import FastAPI

from app.auth import router as auth_router
from app.patients import router as patients_router

app = FastAPI(
    title="GoEcosystem - Gestión de pacientes",
    description="API para gestionar pacientes y su estado de atención.",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(patients_router)


@app.get("/health", tags=["Estado"])
def health():
    return {"status": "ok"}