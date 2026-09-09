from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    business_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="businesses")
    whatsapp_account: Mapped["WhatsAppAccount | None"] = relationship(
        back_populates="business", uselist=False
    )
    contacts: Mapped[list["Contact"]] = relationship(back_populates="business")
    templates: Mapped[list["Template"]] = relationship(back_populates="business")
    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="business")