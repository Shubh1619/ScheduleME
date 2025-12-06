# backend/services/analytics_service.py

from sqlalchemy.orm import Session
from backend.models.post import Post


def get_post_stats_for_user(db: Session, user_id: str):
    # Very simple stub for now
    total_posts = db.query(Post).filter(Post.user_id == user_id).count()
    published = db.query(Post).filter(Post.user_id == user_id, Post.external_post_id.isnot(None)).count()
    return {
        "total_posts": total_posts,
        "published_posts": published,
    }
