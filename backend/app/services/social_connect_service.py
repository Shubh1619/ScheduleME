import httpx
from urllib.parse import urlencode
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.setting import settings
from app.crud.social_account import create_social_account
from app.models.social_account import Provider
from app.core.security import encrypt_token
from app.core.database import get_db


async def get_meta_auth_url(user_id: str) -> str:
    params = {
        "client_id": settings.meta_client_id,
        "redirect_uri": settings.meta_redirect_uri,
        "scope": settings.meta_scopes,
        "response_type": "code",
        "state": user_id  # CSRF + user linking
    }
    return f"https://www.facebook.com/v20.0/dialog/oauth?{urlencode(params)}"


async def exchange_meta_code(code: str, user_id: str, db: AsyncSession = Depends(get_db)):
    async with httpx.AsyncClient() as client:

        # 1️⃣ Exchange code → short-lived token
        token_res = await client.get(
            "https://graph.facebook.com/v20.0/oauth/access_token",
            params={
                "client_id": settings.meta_client_id,
                "client_secret": settings.meta_client_secret,
                "redirect_uri": settings.meta_redirect_uri,
                "code": code
            }
        )
        data = token_res.json()
        if "access_token" not in data:
            raise HTTPException(400, "Token exchange failed")

        short_token = data["access_token"]

        # 2️⃣ Upgrade to long-lived token
        long_res = await client.get(
            "https://graph.facebook.com/v20.0/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.meta_client_id,
                "client_secret": settings.meta_client_secret,
                "fb_exchange_token": short_token
            }
        )
        long_data = long_res.json()
        long_token = long_data.get("access_token", short_token)
        expires_in = long_data.get("expires_in", 5184000)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        # 3️⃣ Fetch Facebook Pages
        pages_res = await client.get(
            "https://graph.facebook.com/v20.0/me/accounts",
            params={"access_token": long_token}
        )
        pages = pages_res.json().get("data", [])

        # 4️⃣ Fetch Instagram Professional Account
        ig_id = None
        for page in pages:
            page_id = page["id"]
            page_token = page["access_token"]

            ig_res = await client.get(
                f"https://graph.facebook.com/v20.0/{page_id}",
                params={
                    "fields": "instagram_business_account",
                    "access_token": page_token
                }
            )
            ig_data = ig_res.json().get("instagram_business_account")
            if ig_data:
                ig_id = ig_data["id"]
                break

        # 5️⃣ Store result in DB
        account_data = {
            "provider": Provider.INSTAGRAM if ig_id else Provider.FACEBOOK,
            "provider_account_id": ig_id or pages[0]["id"],
            "access_token": long_token,
            "refresh_token": None,
            "token_expires_at": expires_at
        }

        return await create_social_account(db, account_data, user_id)
