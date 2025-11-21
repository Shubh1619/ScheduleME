# backend/schemas/social_account.py

from pydantic import BaseModel
from backend.core.constants import ProviderEnum


class SocialAccountBase(BaseModel):
    provider: ProviderEnum
    provider_account_id: str


class SocialAccountRead(SocialAccountBase):
    id: str
    user_id: str

    class Config:
        orm_mode = True
