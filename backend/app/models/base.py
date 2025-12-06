from sqlalchemy import Column, String, DateTime, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from uuid import uuid4

Base = declarative_base()

def default_uuid():
    return str(uuid4())