from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate, UserOut
from app.crud.user import create_user
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.auth_service import login

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await create_user(db, user)
    return UserOut.from_orm(db_user)


@router.post("/login")
async def login_endpoint(identifier: str, password: str, db: AsyncSession = Depends(get_db)):
    return await login(identifier, password, db)


@router.get("/me", response_model=UserOut)
async def read_me(current_user = Depends(get_current_user)):
    return UserOut.from_orm(current_user)
