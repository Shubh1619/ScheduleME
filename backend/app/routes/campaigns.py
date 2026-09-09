import re
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import SessionLocal, get_db
from ..deps import get_business_for_user
from ..models.business import Business
from ..models.campaign import Campaign
from ..models.contact import Contact
from ..models.message import Message
from ..models.whatsapp_account import WhatsAppAccount
from ..schemas import campaign as campaign_schemas
from ..services.whatsapp import WhatsAppError, WhatsAppService

router = APIRouter(prefix="/businesses/{business_id}/campaigns", tags=["campaigns"])

PLACEHOLDER_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def render_template(template: str, contact: Contact) -> str:
    def replace(match: re.Match) -> str:
        key = match.group(1)
        value = contact.attributes.get(key)
        if value is None:
            value = getattr(contact, key, "")
        if not isinstance(value, str):
            value = str(value)
        return value

    return PLACEHOLDER_RE.sub(replace, template)


def process_campaign(campaign_id: int, whatsapp: WhatsAppService) -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        campaign = db.get(Campaign, campaign_id)
        if campaign is None:
            return
        account = db.scalar(
            select(WhatsAppAccount).where(WhatsAppAccount.business_id == campaign.business_id)
        )
        if account is None:
            messages = db.scalars(
                select(Message).where(Message.campaign_id == campaign_id, Message.status == "queued")
            ).all()
            for message in messages:
                message.status = "failed"
                message.error_message = "No WhatsApp account connected to this business"
                message.error_code = "NO_ACCOUNT"
            campaign.status = "completed"
            db.commit()
            return

        messages = db.scalars(
            select(Message)
            .where(Message.campaign_id == campaign_id, Message.status == "queued")
            .order_by(Message.id)
        ).all()
        if not messages:
            campaign.status = "completed"
            db.commit()
            return

        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        daily_sent = db.scalar(
            select(func.count(Message.id))
            .join(Campaign, Campaign.id == Message.campaign_id)
            .where(
                Campaign.business_id == campaign.business_id,
                Message.status == "sent",
                Message.sent_at >= cutoff,
            )
        ) or 0

        interval = 60.0 / max(1, settings.send_messages_per_minute)
        next_slot = 0.0
        sent_this_run = 0
        backoffs = 0

        for message in messages:
            if daily_sent + sent_this_run >= settings.send_daily_limit:
                db.commit()
                campaign = db.get(Campaign, campaign_id)
                if campaign is not None:
                    campaign.status = "paused"
                    db.commit()
                return

            while True:
                wait = next_slot - time.monotonic()
                if wait > 0:
                    time.sleep(wait)
                next_slot = time.monotonic() + interval

                body = render_template(campaign.message_body, message.contact)
                try:
                    wa_id = whatsapp.send_text_message(
                        account.phone_number_id, account.access_token, message.contact.phone, body
                    )
                    message.status = "sent"
                    message.whatsapp_message_id = wa_id
                    message.error_code = None
                    message.error_message = None
                    message.sent_at = datetime.now(timezone.utc)
                    sent_this_run += 1
                    db.commit()
                    break
                except WhatsAppError as exc:
                    if exc.code in WhatsAppService.RATE_LIMIT_CODES:
                        if backoffs >= settings.send_max_backoffs:
                            db.commit()
                            campaign = db.get(Campaign, campaign_id)
                            if campaign is not None:
                                campaign.status = "paused"
                                db.commit()
                            return
                        backoffs += 1
                        time.sleep(settings.send_rate_limit_backoff_seconds)
                        next_slot = time.monotonic() + interval
                        continue
                    message.status = "failed"
                    message.error_code = str(exc.code) if exc.code is not None else "WHATSAPP_ERROR"
                    message.error_message = str(exc)
                    db.commit()
                    break

        campaign = db.get(Campaign, campaign_id)
        if campaign is not None:
            campaign.status = "completed"
            db.commit()
    finally:
        db.close()


@router.post("", response_model=campaign_schemas.CampaignOut, status_code=status.HTTP_201_CREATED)
def create_campaign(
    business_id: int,
    payload: campaign_schemas.CampaignCreate,
    business: Business = Depends(get_business_for_user),
    db: Session = Depends(get_db),
):
    campaign = Campaign(business_id=business_id, **payload.model_dump())
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.get("", response_model=list[campaign_schemas.CampaignOut])
def list_campaigns(
    business_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: str = Query(None, alias="status"),
    business: Business = Depends(get_business_for_user),
    db: Session = Depends(get_db),
):
    stmt = select(Campaign).where(Campaign.business_id == business_id)
    if status_filter:
        stmt = stmt.where(Campaign.status == status_filter)
    campaigns = db.scalars(stmt.order_by(Campaign.created_at.desc()).offset(skip).limit(limit)).all()
    return campaigns


@router.get("/{campaign_id}", response_model=campaign_schemas.CampaignWithStats)
def get_campaign(
    business_id: int,
    campaign_id: int,
    business: Business = Depends(get_business_for_user),
    db: Session = Depends(get_db),
):
    campaign = db.scalar(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.business_id == business_id)
    )
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    rows = db.execute(
        select(Message.status, func.count(Message.id))
        .where(Message.campaign_id == campaign_id)
        .group_by(Message.status)
    ).all()
    counts = {"total": sum(count for _, count in rows)}
    for message_status, count in rows:
        counts[message_status] = count
    stats = campaign_schemas.CampaignStats(**counts)
    data = campaign_schemas.CampaignOut.model_validate(campaign).model_dump()
    return campaign_schemas.CampaignWithStats(**data, stats=stats)


@router.patch("/{campaign_id}", response_model=campaign_schemas.CampaignOut)
def update_campaign(
    business_id: int,
    campaign_id: int,
    payload: campaign_schemas.CampaignUpdate,
    business: Business = Depends(get_business_for_user),
    db: Session = Depends(get_db),
):
    campaign = db.scalar(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.business_id == business_id)
    )
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(campaign, field, value)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
    business_id: int,
    campaign_id: int,
    business: Business = Depends(get_business_for_user),
    db: Session = Depends(get_db),
):
    campaign = db.scalar(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.business_id == business_id)
    )
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    db.delete(campaign)
    db.commit()


@router.post("/{campaign_id}/send", status_code=status.HTTP_202_ACCEPTED)
def send_campaign(
    business_id: int,
    campaign_id: int,
    background_tasks: BackgroundTasks,
    payload: Optional[campaign_schemas.CampaignSendRequest] = None,
    business: Business = Depends(get_business_for_user),
    db: Session = Depends(get_db),
):
    if payload is None:
        payload = campaign_schemas.CampaignSendRequest()
    campaign = db.scalar(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.business_id == business_id)
    )
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    if campaign.status == "sending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Campaign is already sending")
    contact_query = select(Contact).where(
        Contact.business_id == business_id, Contact.opted_in.is_(True)
    )
    if payload.contact_ids:
        contact_query = contact_query.where(Contact.id.in_(payload.contact_ids))
    already_queued = exists(
        select(Message.id).where(
            Message.campaign_id == campaign.id, Message.contact_id == Contact.id
        )
    )
    contact_query = contact_query.where(~already_queued)
    contacts = db.scalars(contact_query).all()
    if not contacts:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No opted-in contacts to send to")
    for contact in contacts:
        db.add(Message(campaign_id=campaign.id, contact_id=contact.id, status="queued"))
    campaign.status = "sending"
    db.commit()
    background_tasks.add_task(process_campaign, campaign.id, WhatsAppService())
    return {"status": "sending", "message": f"Campaign {campaign.id} is being sent to {len(contacts)} contact(s)"}