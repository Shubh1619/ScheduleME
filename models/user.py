# backend/models/user.py

import uuid
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from backend.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    timezone = Column(String, nullable=False, default="UTC")
