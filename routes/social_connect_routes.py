# backend/routes/social_connect_routes.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.oauth_clients import build_oauth_url, exchange_code_for_tokens
from backend.core.security import get_current_user
from backend.db.database import get_db
from backend.services.token_service import store_tokens
from backend.models.user import User

router = APIRouter(prefix="/social", tags=["social"])


@router.get("/connect/{provider}")
def initiate_connection(provider: str, current_user: User = Depends(get_current_user)):
    # Normally generate a 'state' param
    state = "dummy_state"
    url = build_oauth_url(provider, state)
    return {"auth_url": url}


@router.get("/callback/{provider}")
def oauth_callback(
    provider: str,
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tokens = exchange_code_for_tokens(provider, code)
    sa = store_tokens(
        db=db,
        user_id=str(current_user.id),
        provider=provider,
        provider_account_id="provider_user_id",  # TODO: fetch from provider
        access_token=tokens["access_token"],
        refresh_token=tokens.get("refresh_token"),
        token_expires_at=tokens.get("expires_at"),
    )
    return {"message": "Account connected", "social_account_id": str(sa.id)}
