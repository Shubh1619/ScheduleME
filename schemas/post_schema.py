# backend/schemas/post.py

from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

from backend.core.constants import PostStatusEnum


class PostCreate(BaseModel):
    social_account_id: str
    content_text: str
    media_urls: List[str] | None = None
    scheduled_time: datetime  # in UTC or convert on backend


class PostRead(BaseModel):
    id: str
    user_id: str
    social_account_id: str
    content_text: str
    media_urls: Optional[list[str]] = None
    scheduled_time: datetime
    status: PostStatusEnum
    external_post_id: Optional[str] = None

    class Config:
        orm_mode = True
