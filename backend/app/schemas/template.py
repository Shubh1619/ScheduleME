from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TemplateBase(BaseModel):
    template_name: str = Field(min_length=1, max_length=255)
    template_body: str = Field(min_length=1)
    language: str = "en"
    category: str = "MARKETING"


class TemplateCreate(TemplateBase):
    pass


class TemplateOut(TemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    status: str
    created_at: datetime
    updated_at: datetime