from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook
from pwdlib import PasswordHash
from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import EPS, Patient, User


PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXCEL_PATH = PROJECT_ROOT / "data" / "Datos_Sinteticos_Prueba_2026.xlsx"

password_hasher = PasswordHash.recommended()


def read_rows(workbook, sheet_name):
    """Convierte cada fila del Excel en un diccionario."""
    rows = workbook[sheet_name].iter_rows(values_only=True)
    headers = next(rows)

    for row in rows:
        if any(value is not None for value in row):
            yield dict(zip(headers, row))


def required_text(value):
    if value is None or not str(value).strip():
        raise ValueError("Falta un campo de texto obligatorio.")

    return str(value).strip()


def optional_text(value):
    if value is None:
        return None

    return str(value).strip() or None


def parse_datetime(value):
    if isinstance(value, datetime):
        return value

    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())

    return datetime.fromisoformat(required_text(value))


def parse_birth_date(value):
    result = parse_datetime(value).date()

    if result > date.today():
        raise ValueError("La fecha de nacimiento no puede ser futura.")

    return result


def main():
    if not EXCEL_PATH.is_file():
        raise FileNotFoundError(f"No se encontró el Excel: {EXCEL_PATH}")

    workbook = load_workbook(
        EXCEL_PATH,
        read_only=True,
        data_only=True,
    )

    added = {"eps": 0, "users": 0, "patients": 0}

    try:
        with SessionLocal() as session:
            # Una sola transaccion: si algo falla, se revierte la carga.
            with session.begin():
                for row in read_rows(workbook, "Catalogos"):
                    if row.get("eps_codigo") is None:
                        continue

                    code = required_text(row["eps_codigo"])

                    if session.get(EPS, code) is not None:
                        continue

                    session.add(
                        EPS(
                            code=code,
                            name=required_text(row["eps_nombre"]),
                        )
                    )
                    added["eps"] += 1

                session.flush()

                usernames = set(
                    session.scalars(select(User.username)).all()
                )

                for row in read_rows(workbook, "Usuarios_Login"):
                    username = required_text(row["usuario"])

                    if username in usernames:
                        continue

                    session.add(
                        User(
                            username=username,
                            full_name=required_text(row["nombre"]),
                            password_hash=password_hasher.hash(
                                required_text(row["password_demo"])
                            ),
                            role=required_text(row["rol"]),
                            active=str(row["activo"]).strip() == "1",
                        )
                    )
                    usernames.add(username)
                    added["users"] += 1

                documents = set(
                    session.scalars(select(Patient.document)).all()
                )

                for row_number, row in enumerate(
                    read_rows(workbook, "Pacientes"),
                    start=2,
                ):
                    try:
                        document = required_text(row["documento"])

                        if document in documents:
                            continue

                        session.add(
                            Patient(
                                document_type=required_text(
                                    row["tipo_documento"]
                                ),
                                document=document,
                                full_name=required_text(
                                    row["nombre_completo"]
                                ),
                                birth_date=parse_birth_date(
                                    row["fecha_nacimiento"]
                                ),
                                gender=required_text(row["genero"]),
                                phone=required_text(row["telefono"]),
                                email=optional_text(row.get("correo")),
                                city=optional_text(row.get("ciudad")),
                                eps_code=required_text(row["eps_codigo"]),
                                priority=required_text(row["prioridad"]),
                                status=required_text(row["estado"]),
                                created_at=parse_datetime(
                                    row["fecha_creacion"]
                                ),
                                updated_at=parse_datetime(
                                    row["fecha_actualizacion"]
                                ),
                            )
                        )

                        # Valida las restricciones de esta fila.
                        session.flush()
                        documents.add(document)
                        added["patients"] += 1

                    except Exception as exc:
                        raise ValueError(
                            f"Error en la hoja Pacientes, fila {row_number}."
                        ) from exc

            print(f"Registros nuevos: {added}")

            for model in (EPS, User, Patient):
                total = session.scalar(
                    select(func.count()).select_from(model)
                )
                print(f"Total en {model.__tablename__}: {total}")

    finally:
        workbook.close()


if __name__ == "__main__":
    main()