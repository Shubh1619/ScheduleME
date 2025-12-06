from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.user import get_user_by_email_or_mobile
from app.core.security import verify_password, create_access_token
from app.core.database import get_db


async def login(identifier: str, password: str, db: AsyncSession = Depends(get_db)):
    # identifier = can be email OR mobile
    user = await get_user_by_email_or_mobile(db, identifier)

    if not user:
        raise HTTPException(status_code=400, detail="Invalid email/mobile or password")

    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid email/mobile or password")

    token = create_access_token({"sub": user.id})

    return {"access_token": token, "token_type": "bearer"}
