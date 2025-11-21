# backend/routes/webhook_routes.py

from fastapi import APIRouter, Request

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/social/{provider}")
async def social_webhook(provider: str, request: Request):
    body = await request.json()
    # TODO: handle callbacks
    return {"status": "ok"}
