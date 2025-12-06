from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional

from app.models.user import User
from app.core import security


# -----------------------------
# CREATE USER
# -----------------------------
async def create_user(db: AsyncSession, user) -> User:
    """Create a new user with name, mobile, email, and hashed password."""
    
    db_user = User(
        name=user.name,
        mobile=user.mobile,
        email=user.email,
        password_hash=security.get_password_hash(user.password)
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


# -----------------------------
# GET USER BY EMAIL OR MOBILE
# (used in login)
# -----------------------------
async def get_user_by_email_or_mobile(db: AsyncSession, identifier: str) -> Optional[User]:
    """Login using email OR mobile."""
    
    result = await db.execute(
        select(User).where(
            (User.email == identifier) |
            (User.mobile == identifier)
        )
    )
    
    return result.scalar_one_or_none()


# -----------------------------
# GET USER BY ID
# (used by JWT /auth/me)
# -----------------------------
async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
