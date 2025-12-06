from enum import Enum
from sqlalchemy import Column, String, ForeignKey, DateTime ,select
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy import Enum as SQLEnum
from app.core import security

from app.models.base import default_uuid

class Provider(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    # Add more in Phase 3

class SocialAccount(Base):
    __tablename__ = "social_accounts"
    
    id = Column(String, primary_key=True, default=default_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    provider = Column(SQLEnum(Provider))
    provider_account_id = Column(String)  # e.g., Page ID
    access_token = Column(String)  # Encrypted
    refresh_token = Column(String)  # Encrypted
    token_expires_at = Column(DateTime(timezone=True))
    
    user = relationship("User", back_populates="social_accounts")