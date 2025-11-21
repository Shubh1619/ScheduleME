# backend/services/token_service.py

from sqlalchemy.orm import Session
from backend.core.encryption.py import encrypt_value, decrypt_value  # fix path if needed
from backend.models.social_account import SocialAccount


def store_tokens(
    db: Session,
    user_id: str,
    provider: str,
    provider_account_id: str,
    access_token: str,
    refresh_token: str | None = None,
    token_expires_at: str | None = None,
) -> SocialAccount:
    sa = SocialAccount(
        user_id=user_id,
        provider=provider,
        provider_account_id=provider_account_id,
        access_token_encrypted=encrypt_value(access_token),
        refresh_token_encrypted=encrypt_value(refresh_token) if refresh_token else None,
        token_expires_at=token_expires_at,
    )
    db.add(sa)
    db.commit()
    db.refresh(sa)
    return sa
