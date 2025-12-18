from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PublishPostPayload(BaseModel):
    platform: str              # facebook | instagram
    caption: str
    media_url: Optional[str] = None
    scheduled_at: Optional[datetime] = None
