from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    # Guardamos las fechas y horas en UTC.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('ADMIN', 'OPERADOR')",
            name="ck_users_role",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="OPERADOR"
    )
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )


class EPS(Base):
    __tablename__ = "eps"

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(
        String(150), unique=True, nullable=False
    )

    patients: Mapped[list["Patient"]] = relationship(
        back_populates="eps"
    )


class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = (
        CheckConstraint(
            "document_type IN ('CC', 'TI', 'CE', 'PA')",
            name="ck_patients_document_type",
        ),
        CheckConstraint(
            "gender IN ('Femenino', 'Masculino', 'Otro')",
            name="ck_patients_gender",
        ),
        CheckConstraint(
            "priority IN ('Alta', 'Media', 'Baja')",
            name="ck_patients_priority",
        ),
        CheckConstraint(
            "status IN ('Pendiente', 'En atención', 'Atendido')",
            name="ck_patients_status",
        ),
        CheckConstraint(
            "length(trim(full_name)) BETWEEN 2 AND 150",
            name="ck_patients_full_name",
        ),
        CheckConstraint(
            "length(trim(document)) BETWEEN 1 AND 20",
            name="ck_patients_document",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_type: Mapped[str] = mapped_column(
        String(3), nullable=False
    )
    document: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(
        String(150), nullable=False, index=True
    )
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    phone: Mapped[str] = mapped_column(String(25), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254))
    city: Mapped[str | None] = mapped_column(String(100))

    eps_code: Mapped[str] = mapped_column(
        ForeignKey("eps.code", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        String(10), nullable=False, default="Media", index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Pendiente", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    eps: Mapped["EPS"] = relationship(back_populates="patients")