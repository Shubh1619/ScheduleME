from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import default_uuid

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=default_uuid)
    name = Column(String, nullable=False)
    mobile = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    social_accounts = relationship(
        "SocialAccount",
        back_populates="user",
        cascade="all, delete-orphan"
    )
