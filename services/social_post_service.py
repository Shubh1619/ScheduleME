# backend/services/social_post_service.py

"""
This is where you'll call Facebook / Instagram / LinkedIn / X APIs
using the decrypted tokens.

For now, it's a stub to keep workers simple.
"""

from backend.models.post import Post


def publish_to_provider(post: Post, access_token: str) -> str:
    """
    TODO: Implement provider-specific logic here.
    Return external_post_id from provider.
    """
    # Example: call LinkedIn / Facebook / etc.
    return "external_post_id_dummy"
