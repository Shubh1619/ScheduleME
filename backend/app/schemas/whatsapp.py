from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConnectRequest(BaseModel):
    business_id: int


class ConnectOut(BaseModel):
    auth_url: str
    state: str


class WhatsAppAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    waba_id: str
    phone_number_id: str
    phone_number: str
    display_name: str
    status: str
    created_at: datetime
    updated_at: datetime