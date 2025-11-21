# backend/routes/analytics_routes.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.core.security import get_current_user
from backend.services.analytics_service import get_post_stats_for_user
from backend.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/me")
def my_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_post_stats_for_user(db, user_id=str(current_user.id))
