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
from sqlalchemy import select
from app.models.social_account import SocialAccount  # ensure correct import



async def get_meta_auth_url(user_id: str) -> str:
    params = {
        "client_id": settings.meta_client_id,
        "redirect_uri": settings.meta_redirect_uri,   # IMPORTANT
        "scope": settings.meta_scopes,
        "response_type": "code",
        "state": user_id
    }
    return f"https://www.facebook.com/v20.0/dialog/oauth?{urlencode(params)}"


async def exchange_meta_code(code: str, user_id: str, db: AsyncSession):
    async with httpx.AsyncClient() as client:

        # 1️⃣ SHORT-LIVED TOKEN
        token_res = await client.get(
            "https://graph.facebook.com/v20.0/oauth/access_token",
            params={
                "client_id": settings.meta_client_id,
                "client_secret": settings.meta_client_secret,
                "redirect_uri": settings.meta_redirect_uri,
                "code": code,
            },
        )
        data = token_res.json()
        if "access_token" not in data:
            raise HTTPException(400, f"Token exchange failed: {data}")

        short_token = data["access_token"]

        # 2️⃣ LONG-LIVED USER TOKEN
        ll_res = await client.get(
            "https://graph.facebook.com/v20.0/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.meta_client_id,
                "client_secret": settings.meta_client_secret,
                "fb_exchange_token": short_token,
            },
        )
        ll_data = ll_res.json()
        long_user_token = ll_data.get("access_token", short_token)
        expires_at = datetime.utcnow() + timedelta(seconds=ll_data.get("expires_in", 5184000))

        print("\n===== TOKEN DETAILS =====")
        print("Short Token:", repr(short_token))
        print("Long Token:", repr(long_user_token))

        # 3️⃣ GET FACEBOOK PAGES
        pages_res = await client.get(
            "https://graph.facebook.com/v20.0/me/accounts",
            params={"access_token": long_user_token},
        )
        raw_pages = pages_res.json()
        pages = raw_pages.get("data", [])

        print("\n===== RAW PAGES =====")
        print(raw_pages)

        # 4️⃣ FILTER ONLY PAGES WITH VALID TOKEN
        valid_pages = [p for p in pages if p.get("access_token")]

        if not valid_pages:
            raise HTTPException(
                400,
                "No valid Facebook Pages found. Ensure required permissions are granted."
            )

        page = valid_pages[0]
        page_id = page["id"]
        page_token = page["access_token"]

        print("\n===== PAGE SELECTED =====")
        print("Page ID:", page_id)
        print("Page Token:", repr(page_token))

        # 5️⃣ CHECK IG BUSINESS ACCOUNT
        ig_res = await client.get(
            f"https://graph.facebook.com/v20.0/{page_id}",
            params={
                "fields": "instagram_business_account",
                "access_token": page_token,
            },
        )
        ig_data = ig_res.json().get("instagram_business_account")
        ig_id = ig_data["id"] if ig_data else None

        provider_account_id = ig_id if ig_id else page_id
        provider_type = Provider.INSTAGRAM if ig_id else Provider.FACEBOOK

        # 6️⃣ UPSERT → UPDATE IF EXISTS
        existing_query = select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.provider == provider_type,
            SocialAccount.provider_account_id == provider_account_id
        )
        existing = await db.execute(existing_query)
        existing_account = existing.scalars().first()

        if existing_account:
            print("===== UPDATING EXISTING ACCOUNT =====")
            existing_account.access_token = page_token
            existing_account.token_expires_at = expires_at
            await db.commit()
            await db.refresh(existing_account)
            return existing_account

        # 7️⃣ CREATE NEW ACCOUNT
        print("===== CREATING NEW ACCOUNT =====")
        account_data = {
            "provider": provider_type,
            "provider_account_id": provider_account_id,
            "access_token": page_token,
            "refresh_token": None,
            "token_expires_at": expires_at,
        }

        return await create_social_account(db, account_data, user_id)


async def get_connected_accounts(user_id: str, db: AsyncSession):
    """
    Returns all connected accounts with live Meta data.
    Safely handles invalid/expired tokens.
    """

    # Fetch all accounts
    query = select(SocialAccount).where(SocialAccount.user_id == user_id)
    result = await db.execute(query)
    accounts = result.scalars().all()

    output = []

    async with httpx.AsyncClient() as client:
        for acc in accounts:
            provider = acc.provider.value
            provider_id = acc.provider_account_id
            access_token = acc.access_token

            enriched = {"error": None, "data": None}

            try:
                if provider == "facebook":
                    res = await client.get(
                        f"https://graph.facebook.com/v20.0/{provider_id}",
                        params={
                            "fields": "id,name,link,fan_count,about",
                            "access_token": access_token
                        }
                    )
                else:
                    res = await client.get(
                        f"https://graph.facebook.com/v20.0/{provider_id}",
                        params={
                            "fields": "id,username,profile_picture_url,followers_count,follows_count,media_count",
                            "access_token": access_token
                        }
                    )

                json_data = res.json()

                if "error" in json_data:
                    enriched["error"] = json_data["error"]
                else:
                    enriched["data"] = json_data

            except Exception as e:
                enriched["error"] = {"message": str(e)}

            output.append({
                "db_id": acc.id,
                "provider": provider,
                "provider_account_id": provider_id,
                "token_expires_at": acc.token_expires_at.isoformat() if acc.token_expires_at else None,
                "meta_data": enriched,
            })

    return output
