from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models.message import Message

router = APIRouter(prefix="/webhook", tags=["webhook"])

DELIVERY_STATUSES = {"sent", "delivered", "read", "failed"}


@router.get("")
def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    verify_token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge"),
):
    settings = get_settings()
    if mode == "subscribe" and verify_token == settings.whatsapp_webhook_verify_token:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Webhook verification failed")


@router.post("", status_code=status.HTTP_200_OK)
def receive_webhook(payload: Dict[str, Any], db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for status_event in value.get("statuses", []):
                message_id = status_event.get("id")
                state = status_event.get("status")
                if not message_id or state not in DELIVERY_STATUSES:
                    continue
                message = db.scalar(select(Message).where(Message.whatsapp_message_id == message_id))
                if message is None:
                    continue
                if state == "sent":
                    message.status = "sent"
                    if message.sent_at is None:
                        message.sent_at = now
                elif state == "delivered":
                    message.status = "delivered"
                    message.delivered_at = now
                elif state == "read":
                    message.status = "read"
                    message.read_at = now
                elif state == "failed":
                    message.status = "failed"
                    errors = status_event.get("errors", [])
                    if errors:
                        message.error_code = str(errors[0].get("code", ""))
                        message.error_message = str(errors[0].get("message", ""))
    db.commit()
    return {"status": "received"}