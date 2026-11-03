import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


DocumentType = Literal["CC", "TI", "CE", "PA"]
Gender = Literal[
    "Femenino",
    "Masculino",
    "Otro",
    "Prefiere no informar",
]
Priority = Literal["Alta", "Media", "Baja"]
PatientStatus = Literal["Pendiente", "En atención", "Atendido"]


class PatientBase(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    document_type: DocumentType
    document: str = Field(min_length=1, max_length=20)
    full_name: str = Field(min_length=2, max_length=150)
    birth_date: date
    gender: Gender
    phone: str = Field(min_length=7, max_length=25)
    email: str | None = Field(default=None, max_length=254)
    city: str | None = Field(default=None, max_length=100)
    eps_code: str = Field(min_length=1, max_length=10)
    priority: Priority = "Media"
    status: PatientStatus = "Pendiente"

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError(
                "La fecha de nacimiento no puede ser futura."
            )
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not re.fullmatch(r"\+?[0-9 ()-]+", value):
            raise ValueError(
                "El teléfono contiene caracteres no permitidos."
            )

        digits = re.sub(r"\D", "", value)

        if not 7 <= len(digits) <= 15:
            raise ValueError(
                "El teléfono debe contener entre 7 y 15 dígitos."
            )

        return value

    @field_validator("email", "city", mode="before")
    @classmethod
    def normalize_optional_text(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            value,
        ):
            raise ValueError("El correo no tiene un formato válido.")

        return value


class PatientCreate(PatientBase):
    """Datos necesarios para registrar un paciente."""


class PatientUpdate(PatientBase):
    """Datos completos para actualizar un paciente mediante PUT."""


class EPSResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str


class PatientResponse(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    eps: EPSResponse


class PatientListResponse(BaseModel):
    items: list[PatientResponse]
    total: int
    page: int
    page_size: int


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: str


class DashboardResponse(BaseModel):
    total_patients: int
    pending_patients: int
    in_care_patients: int
    attended_patients: int
    high_priority_patients: int