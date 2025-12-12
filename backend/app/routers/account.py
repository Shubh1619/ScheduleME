from fastapi import APIRouter, Depends, HTTPException
from app.services.social_connect_service import get_meta_auth_url, exchange_meta_code,get_connected_accounts
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.security import get_current_user

router = APIRouter(tags=["accounts"])

@router.get("/meta/auth-url")
async def meta_auth_url(current_user: User = Depends(get_current_user)):
    return {"auth_url": await get_meta_auth_url(current_user.id)}

@router.get("/connect/meta/callback")
async def meta_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    
    # Authenticate using STATE, not JWT
    user = await db.get(User, state)
    if not user:
        raise HTTPException(400, "Invalid state — user not found")

    account = await exchange_meta_code(code, user.id, db)

    return {
        "message": "Meta account connected successfully 🎉",
        "account_id": account.id,
        "provider": account.provider.value
    }


@router.get("/connected/accounts")
async def connected_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    accounts = await get_connected_accounts(current_user.id, db)
    return {"accounts": accounts}