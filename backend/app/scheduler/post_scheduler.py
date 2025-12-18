from datetime import datetime
from services.post_publisher import (
    publish_to_instagram,
    publish_to_facebook
)

def execute_scheduled_post(payload):
    if payload.platform == "instagram":
        return publish_to_instagram(payload)
    elif payload.platform == "facebook":
        return publish_to_facebook(payload)
    else:
        raise ValueError("Unsupported platform")
