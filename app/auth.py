from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, TokenResponse, UserResponse
from app.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    get_current_user,
    password_hasher,
)


router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.username == credentials.username)
    )

    stored_hash = (
        user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    )

    password_valid = password_hasher.verify(
        credentials.password,
        stored_hash,
    )

    if user is None or not password_valid or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=create_access_token(user.id)
    )


@router.get("/me", response_model=UserResponse)
def me(
    current_user: User = Depends(get_current_user),
):
    return current_user