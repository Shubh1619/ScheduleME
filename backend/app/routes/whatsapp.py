from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..deps import get_current_user
from ..models.business import Business
from ..models.user import User
from ..models.whatsapp_account import WhatsAppAccount
from ..schemas.whatsapp import ConnectOut, ConnectRequest, WhatsAppAccountOut
from ..services.security import create_state_token, decode_token
from ..services.whatsapp import WhatsAppError, WhatsAppService

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

whatsapp_service = WhatsAppService()


def _owned_business(business_id: int, user: User, db: Session) -> Business:
    business = db.get(Business, business_id)
    if business is None or business.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return business


def _existing_account(business: Business, db: Session) -> WhatsAppAccount | None:
    return db.scalar(select(WhatsAppAccount).where(WhatsAppAccount.business_id == business.id))


@router.post("/connect", response_model=ConnectOut)
def start_connect(payload: ConnectRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    business = _owned_business(payload.business_id, user, db)
    if _existing_account(business, db):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="WhatsApp already connected")
    state = create_state_token(business.id)
    try:
        auth_url = whatsapp_service.build_onboarding_url(state)
    except WhatsAppError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return ConnectOut(auth_url=auth_url, state=state)


@router.get("/callback", response_model=WhatsAppAccountOut)
def complete_connect(code: str = Query(...), state: str = Query(...), db: Session = Depends(get_db)):
    payload = decode_token(state)
    if payload is None or payload.get("type") != "onboarding":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state")
    business = db.get(Business, int(payload["bid"]))
    if business is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Business not found")
    account = _existing_account(business, db)
    if account:
        return account
    try:
        token = whatsapp_service.exchange_code(code)
        info = whatsapp_service.fetch_whatsapp_account(token)
    except (WhatsAppError, KeyError, IndexError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Meta onboarding failed: {exc}")
    account = WhatsAppAccount(business_id=business.id, status="connected", access_token=token, **info)
    db.add(account)
    db.commit()
    db.refresh(account)
    settings = get_settings()
    return RedirectResponse(f"{settings.frontend_base_url}/dashboard/whatsapp?connected=1")


@router.get("/account", response_model=WhatsAppAccountOut)
def get_account(business_id: int = Query(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    business = _owned_business(business_id, user, db)
    account = _existing_account(business, db)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WhatsApp not connected")
    return account


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
def disconnect(business_id: int = Query(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    business = _owned_business(business_id, user, db)
    account = _existing_account(business, db)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WhatsApp not connected")
    db.delete(account)
    db.commit()