# backend/core/constants.py

from enum import Enum


class ProviderEnum(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"   # X


class PostStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    FAILED_AUTH = "FAILED_AUTH"
