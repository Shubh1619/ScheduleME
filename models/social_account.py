# backend/models/social_account.py

import uuid
from sqlalchemy import Column, String, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.db.database import Base
from backend.core.constants import ProviderEnum


class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    provider = Column(Enum(ProviderEnum), nullable=False)
    provider_account_id = Column(String, nullable=False)
    access_token_encrypted = Column(String, nullable=False)
    refresh_token_encrypted = Column(String, nullable=True)
    token_expires_at = Column(String, nullable=True)  # ISO string or timestamp

    user = relationship("User", backref="social_accounts")
