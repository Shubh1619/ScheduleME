from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

CampaignStatus = Literal["draft", "sending", "completed", "paused", "cancelled"]


class CampaignBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    message_body: str = Field(min_length=1, description="Supports placeholders like {{name}} and {{phone}}")
    template_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    message_body: Optional[str] = None
    template_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[CampaignStatus] = None


class CampaignOut(CampaignBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    status: str
    created_at: datetime
    updated_at: datetime


class CampaignSendRequest(BaseModel):
    contact_ids: Optional[List[int]] = None


class CampaignStats(BaseModel):
    total: int
    queued: int = 0
    sent: int = 0
    delivered: int = 0
    read: int = 0
    failed: int = 0


class CampaignWithStats(CampaignOut):
    stats: CampaignStats