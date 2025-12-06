from enum import Enum
from sqlalchemy import Column, Text, ARRAY, String, ForeignKey, DateTime
from app.core.database import Base
from app.core.base import default_uuid

class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(String, primary_key=True, default=default_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    social_account_id = Column(String, ForeignKey("social_accounts.id"))
    content_text = Column(Text)
    media_urls = Column(ARRAY(String))  # S3/R2 URLs (Phase 2)
    scheduled_time = Column(DateTime(timezone=True))  # UTC
    status = Column(SQLEnum(PostStatus), default=PostStatus.DRAFT)
    external_post_id = Column(String)  # From platform API
    created_at = Column(DateTime(timezone=True), server_default=func.now())