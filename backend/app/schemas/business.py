from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BusinessCreate(BaseModel):
    business_name: str = Field(min_length=1, max_length=255)


class BusinessOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    business_name: str
    created_at: datetime
    updated_at: datetime