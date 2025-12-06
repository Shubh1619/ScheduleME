# backend/core/oauth_clients.py

"""
Helpers/placeholders for building provider-specific OAuth URLs & exchanging codes.
Implement real provider logic here later.
"""

from backend.config import get_settings

settings = get_settings()


def build_oauth_url(provider: str, state: str) -> str:
    # TODO: implement per provider
    return f"https://example.com/oauth/{provider}?state={state}"


def exchange_code_for_tokens(provider: str, code: str) -> dict:
    # TODO: call provider token endpoint
    # Return dict containing access_token, refresh_token, expires_at
    return {
        "access_token": "dummy_access",
        "refresh_token": "dummy_refresh",
        "expires_at": None,
    }
