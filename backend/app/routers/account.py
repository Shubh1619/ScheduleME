from fastapi import APIRouter, Depends, Query
from app.services.social_connect_service import get_meta_auth_url, exchange_meta_code
from app.core.database import get_db
from app.core.security import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("/meta/auth-url")
async def meta_auth_url(current_user: User = Depends(get_current_user)):
    return {"auth_url": await get_meta_auth_url(current_user.id)}


@router.get("/meta/callback")
async def meta_callback(code: str, state: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if state != current_user.id:
        raise HTTPException(400, "Invalid state")

    account = await exchange_meta_code(code, current_user.id, db)
    return {"account_id": account.id, "provider": account.provider.value}
