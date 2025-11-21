# backend/models/post.py

import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from backend.db.database import Base
from backend.core.constants import PostStatusEnum


class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    social_account_id = Column(UUID(as_uuid=True), ForeignKey("social_accounts.id"), nullable=False)

    content_text = Column(Text, nullable=False)
    media_urls = Column(ARRAY(String), nullable=True)

    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(PostStatusEnum), default=PostStatusEnum.SCHEDULED, nullable=False)
    external_post_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
