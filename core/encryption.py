# backend/core/encryption.py

from cryptography.fernet import Fernet
from backend.config import get_settings

_settings = get_settings()

# In real production, keep this in env & do NOT hardcode
FERNET_KEY = Fernet.generate_key()
fernet = Fernet(FERNET_KEY)


def encrypt_value(raw: str) -> str:
    return fernet.encrypt(raw.encode("utf-8")).decode("utf-8")


def decrypt_value(token: str) -> str:
    return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
