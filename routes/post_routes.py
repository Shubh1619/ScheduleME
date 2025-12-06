# backend/routes/post_routes.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.schemas.post import PostCreate, PostRead
from backend.services.post_service import create_post, get_posts_for_user
from backend.services.schedule_service import schedule_post_task
from backend.core.security import get_current_user
from backend.models.user import User

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/", response_model=PostRead)
def create_scheduled_post(
    data: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = create_post(db, user_id=str(current_user.id), data=data)
    schedule_post_task(str(post.id), post.scheduled_time)
    return post


@router.get("/", response_model=list[PostRead])
def list_my_posts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    posts = get_posts_for_user(db, user_id=str(current_user.id))
    return posts
