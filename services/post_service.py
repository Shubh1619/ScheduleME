# backend/services/post_service.py

from sqlalchemy.orm import Session
from datetime import datetime

from backend.models.post import Post
from backend.schemas.post import PostCreate


def create_post(db: Session, user_id: str, data: PostCreate) -> Post:
    post = Post(
        user_id=user_id,
        social_account_id=data.social_account_id,
        content_text=data.content_text,
        media_urls=data.media_urls,
        scheduled_time=data.scheduled_time,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def get_posts_for_user(db: Session, user_id: str):
    return db.query(Post).filter(Post.user_id == user_id).order_by(Post.scheduled_time.desc()).all()


def get_scheduled_posts_in_window(db: Session, start: datetime, end: datetime):
    return (
        db.query(Post)
        .filter(Post.scheduled_time >= start, Post.scheduled_time <= end)
        .all()
    )
