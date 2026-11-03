from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Patient
from app.schemas import DashboardResponse
from app.security import get_current_user


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)):
    statement = select(
        func.count(Patient.id).label("total_patients"),
        func.count(
            case((Patient.status == "Pendiente", 1))
        ).label("pending_patients"),
        func.count(
            case((Patient.status == "En atención", 1))
        ).label("in_care_patients"),
        func.count(
            case((Patient.status == "Atendido", 1))
        ).label("attended_patients"),
        func.count(
            case((Patient.priority == "Alta", 1))
        ).label("high_priority_patients"),
    )

    return dict(db.execute(statement).mappings().one())