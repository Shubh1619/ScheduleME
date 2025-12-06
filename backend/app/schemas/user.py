from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    name: str
    mobile: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

    class Config:
        from_attributes = True

class UserOut(UserBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
