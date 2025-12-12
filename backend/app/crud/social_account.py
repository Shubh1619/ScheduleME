from app.models.social_account import SocialAccount
from app.core.security import encrypt_token
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional 
from sqlalchemy import select
from app.core import security


async def create_social_account(db: AsyncSession, account_data: dict, user_id: str) -> SocialAccount:
    # Encrypt tokens before storage
    encrypted_access = encrypt_token(account_data["access_token"])
    encrypted_refresh = encrypt_token(account_data["refresh_token"]) if account_data.get("refresh_token") else None
    
    db_account = SocialAccount(
        user_id=user_id,
        provider=account_data["provider"],
        provider_account_id=account_data["provider_account_id"],
        access_token=encrypted_access,
        refresh_token=encrypted_refresh,
        token_expires_at=account_data["token_expires_at"]
    )
    db.add(db_account)
    await db.commit()
    await db.refresh(db_account)
    return db_account

async def get_social_account(db: AsyncSession, account_id: str) -> Optional[SocialAccount]:
    result = await db.execute(select(SocialAccount).where(SocialAccount.id == account_id))
    account = result.scalar_one_or_none()
    if account:
        # Decrypt on fetch
        account.access_token = security.decrypt_token(account.access_token)
        if account.refresh_token:
            account.refresh_token = security.decrypt_token(account.refresh_token)
    return account