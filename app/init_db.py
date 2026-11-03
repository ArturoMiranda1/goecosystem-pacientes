from app.database import Base, engine
from app import models  # Registra los modelos antes de crear las tablas.


def main():
    Base.metadata.create_all(bind=engine)
    print("Base de datos y tablas creadas correctamente.")


if __name__ == "__main__":
    main()