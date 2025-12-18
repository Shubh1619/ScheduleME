from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.social_account import SocialAccount, Provider
from app.schemas.post import PublishPostPayload



router = APIRouter(prefix="/meta", tags=["Posts"])


@router.get("/facebook/posts")
async def get_facebook_posts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user.id  # 🔥 FIXED

    query = select(SocialAccount).where(
        SocialAccount.user_id == user_id,
        SocialAccount.provider == Provider.FACEBOOK
    )
    result = await db.execute(query)
    acc = result.scalars().first()

    if not acc:
        raise HTTPException(400, "No Facebook Page connected.")

    page_id = acc.provider_account_id
    page_token = acc.access_token

    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"https://graph.facebook.com/v20.0/{page_id}/posts",
            params={
                "fields": "id,message,created_time,permalink_url,attachments{media_type,media_url}",
                "access_token": page_token
            }
        )
        return res.json()


@router.get("/instagram/posts")
async def get_instagram_posts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user.id  # 🔥 FIXED

    query = select(SocialAccount).where(
        SocialAccount.user_id == user_id,
        SocialAccount.provider == Provider.INSTAGRAM
    )
    result = await db.execute(query)
    acc = result.scalars().first()

    if not acc:
        raise HTTPException(400, "No Instagram Business Account connected.")

    ig_id = acc.provider_account_id
    access_token = acc.access_token

    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"https://graph.facebook.com/v20.0/{ig_id}/media",
            params={
                "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp",
                "access_token": access_token
            }
        )

        return res.json()

@router.post("/publish-now")
async def publish_now(
    payload: PublishPostPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    platform = payload.platform.lower()

    if platform not in ["facebook", "instagram"]:
        raise HTTPException(400, "Unsupported platform")

    provider = (
        Provider.FACEBOOK if platform == "facebook"
        else Provider.INSTAGRAM
    )

    query = select(SocialAccount).where(
        SocialAccount.user_id == current_user.id,
        SocialAccount.provider == provider
    )
    result = await db.execute(query)
    acc = result.scalars().first()

    if not acc:
        raise HTTPException(400, f"{platform.capitalize()} account not connected")

    async with httpx.AsyncClient() as client:

        # 🔵 FACEBOOK POST
        if platform == "facebook":
            res = await client.post(
                f"https://graph.facebook.com/v20.0/{acc.provider_account_id}/feed",
                data={
                    "message": payload.caption,
                    "access_token": acc.access_token
                }
            )

        # 🟣 INSTAGRAM POST
        else:
            # Step 1: Create media container
            container = await client.post(
                f"https://graph.facebook.com/v20.0/{acc.provider_account_id}/media",
                data={
                    "image_url": payload.media_url,
                    "caption": payload.caption,
                    "access_token": acc.access_token
                }
            )

            container_id = container.json().get("id")
            if not container_id:
                raise HTTPException(400, "Failed to create IG media container")

            # Step 2: Publish container
            res = await client.post(
                f"https://graph.facebook.com/v20.0/{acc.provider_account_id}/media_publish",
                data={
                    "creation_id": container_id,
                    "access_token": acc.access_token
                }
            )

    return {
        "status": "published",
        "platform": platform,
        "response": res.json()
    }


@router.post("/schedule")
async def schedule_post(
    payload: PublishPostPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not payload.scheduled_at:
        raise HTTPException(400, "scheduled_at is required")

    if payload.platform.lower() not in ["facebook", "instagram"]:
        raise HTTPException(400, "Unsupported platform")

    # 👉 Save to DB here (recommended)
    # ScheduledPost(
    #   user_id=current_user.id,
    #   platform=payload.platform,
    #   caption=payload.caption,
    #   media_url=payload.media_url,
    #   scheduled_at=payload.scheduled_at
    # )

    return {
        "status": "scheduled",
        "platform": payload.platform,
        "scheduled_at": payload.scheduled_at
    }
