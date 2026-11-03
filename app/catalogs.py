from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EPS
from app.schemas import EPSResponse
from app.security import get_current_user


router = APIRouter(
    prefix="/catalogs",
    tags=["Catálogos"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/eps", response_model=list[EPSResponse])
def list_eps(db: Session = Depends(get_db)):
    return db.scalars(
        select(EPS).order_by(EPS.name)
    ).all()