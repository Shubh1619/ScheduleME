# backend/services/auth_service.py

from sqlalchemy.orm import Session

from backend.core.hashing import hash_password, verify_password
from backend.core.security import create_access_token
from backend.models.user import User


def register_user(db: Session, email: str, password: str, timezone: str) -> User:
    user = User(email=email, password_hash=hash_password(password), timezone=timezone)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> str | None:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    token = create_access_token({"sub": str(user.id)})
    return token
