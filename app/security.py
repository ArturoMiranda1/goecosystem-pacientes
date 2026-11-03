import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.database import PROJECT_ROOT, get_db
from app.models import User


load_dotenv(PROJECT_ROOT / ".env")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")

if len(SECRET_KEY) < 32:
    raise RuntimeError(
        "Configura JWT_SECRET_KEY en .env con una clave "
        "aleatoria de al menos 32 caracteres."
    )

ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60

password_hasher = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)

# Permite verificar un hash incluso si el usuario no existe.
DUMMY_PASSWORD_HASH = password_hasher.hash("dummy-password")


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "iat", "exp"]},
        )

        user_id = int(payload["sub"])

    except (InvalidTokenError, ValueError, TypeError):
        raise unauthorized

    user = db.get(User, user_id)

    if user is None or not user.active:
        raise unauthorized

    return user