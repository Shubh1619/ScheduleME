from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models.business import Business
from ..models.user import User
from ..schemas import user as auth_schemas
from ..services.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_token_response(user: User):
    return auth_schemas.TokenOut(
        access_token=create_access_token(user.id),
        token_type="bearer",
        user=auth_schemas.UserOut.model_validate(user),
    )


@router.post("/register", response_model=auth_schemas.TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: auth_schemas.RegisterRequest, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        name=payload.name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    if payload.business_name:
        db.add(Business(user_id=user.id, business_name=payload.business_name))
    db.commit()
    db.refresh(user)
    return _build_token_response(user)


@router.post("/login", response_model=auth_schemas.TokenOut)
def login(payload: auth_schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _build_token_response(user)


@router.get("/me", response_model=auth_schemas.UserOut)
def me(user: User = Depends(get_current_user)):
    return user