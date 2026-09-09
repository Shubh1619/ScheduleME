from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalize_phone(value: str) -> str:
    value = value.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if value.startswith("00"):
        value = "+" + value[2:]
    elif not value.startswith("+"):
        value = "+" + value
    if not value.lstrip("+").isdigit():
        raise ValueError("phone must contain only digits")
    return value


class ContactBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str = Field(description="Phone number in E.164 format, e.g. +14155552671")
    attributes: dict[str, Any] = Field(default_factory=dict)
    opted_in: bool = True

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return _normalize_phone(value)


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    phone: Optional[str] = None
    attributes: Optional[dict[str, Any]] = None
    opted_in: Optional[bool] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_phone(value) if value is not None else None


class ContactOut(ContactBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    created_at: datetime
    updated_at: datetime


class BulkContactResult(BaseModel):
    created: int
    skipped: int
    errors: list[str]