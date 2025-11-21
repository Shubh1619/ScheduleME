# backend/utils/platform_payload_builder.py

"""
Placeholder: build provider-specific payloads from Post objects.
"""


def build_payload_for_provider(provider: str, content_text: str, media_urls: list[str] | None):
    return {
        "text": content_text,
        "media": media_urls or [],
    }
