from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
from app.models.user import User
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.social_account import SocialAccount, Provider

router = APIRouter(prefix="/meta", tags=["Meta Posts"])


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
