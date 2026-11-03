from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import EPS, Patient
from app.schemas import (
    PatientCreate,
    PatientListResponse,
    PatientResponse,
    PatientStatus,
    PatientUpdate,
    Priority,
)
from app.security import get_current_user


router = APIRouter(
    prefix="/patients",
    tags=["Pacientes"],
    dependencies=[Depends(get_current_user)],
)


def get_patient_or_404(db: Session, patient_id: int) -> Patient:
    patient = db.scalar(
        select(Patient)
        .options(joinedload(Patient.eps))
        .where(Patient.id == patient_id)
    )

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Paciente no encontrado.",
        )

    return patient


def validate_references(
    db: Session,
    data: PatientCreate | PatientUpdate,
    patient_id: int | None = None,
):
    if db.get(EPS, data.eps_code) is None:
        raise HTTPException(
            status_code=422,
            detail="La EPS seleccionada no existe.",
        )

    statement = select(Patient.id).where(
        Patient.document == data.document
    )

    if patient_id is not None:
        statement = statement.where(Patient.id != patient_id)

    if db.scalar(statement) is not None:
        raise HTTPException(
            status_code=409,
            detail="Ya existe un paciente con ese documento.",
        )


def save_changes(db: Session):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "No se pudo guardar el registro. Verifica que el "
                "documento no esté duplicado y que la EPS exista."
            ),
        ) from exc


@router.get("", response_model=PatientListResponse)
def list_patients(
    search: str | None = Query(default=None, max_length=150),
    status: PatientStatus | None = None,
    priority: Priority | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    filters = []

    if search and search.strip():
        # autoescape evita interpretar % y _ como comodines.
        term = search.strip()
        filters.append(
            or_(
                Patient.full_name.icontains(term, autoescape=True),
                Patient.document.icontains(term, autoescape=True),
            )
        )

    if status is not None:
        filters.append(Patient.status == status)

    if priority is not None:
        filters.append(Patient.priority == priority)

    total = db.scalar(
        select(func.count())
        .select_from(Patient)
        .where(*filters)
    )

    patients = db.scalars(
        select(Patient)
        .options(joinedload(Patient.eps))
        .where(*filters)
        .order_by(Patient.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return {
        "items": patients,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
):
    return get_patient_or_404(db, patient_id)


@router.post(
    "",
    response_model=PatientResponse,
    status_code=201,
)
def create_patient(
    data: PatientCreate,
    db: Session = Depends(get_db),
):
    validate_references(db, data)

    patient = Patient(**data.model_dump())
    db.add(patient)
    save_changes(db)

    return get_patient_or_404(db, patient.id)


@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: int,
    data: PatientUpdate,
    db: Session = Depends(get_db),
):
    patient = get_patient_or_404(db, patient_id)
    validate_references(db, data, patient_id=patient_id)

    for field, value in data.model_dump().items():
        setattr(patient, field, value)

    save_changes(db)

    # Recarga también la relación si cambió la EPS.
    db.expire(patient)

    return get_patient_or_404(db, patient_id)


@router.delete("/{patient_id}", status_code=204)
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
):
    patient = get_patient_or_404(db, patient_id)

    db.delete(patient)
    save_changes(db)

    return Response(status_code=204)