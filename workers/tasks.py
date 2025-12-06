# backend/workers/tasks.py

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.celery_app import celery_app
from backend.db.database import SessionLocal
from backend.models.post import Post
from backend.core.constants import PostStatusEnum
from backend.utils.logger import logger
from backend.services.social_post_service import publish_to_provider
from backend.core.encryption import decrypt_value
from backend.models.social_account import SocialAccount
from backend.utils.notify import notify_user


def _get_db() -> Session:
    return SessionLocal()


@celery_app.task(name="backend.workers.tasks.publish_post_task")
def publish_post_task(post_id: str):
    db = _get_db()
    try:
        post: Post | None = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            logger.error("Post not found: %s", post_id)
            return

        sa: SocialAccount | None = db.query(SocialAccount).filter(SocialAccount.id == post.social_account_id).first()
        if not sa:
            logger.error("SocialAccount not found for post: %s", post_id)
            return

        access_token = decrypt_value(sa.access_token_encrypted)
        external_post_id = publish_to_provider(post, access_token)

        post.status = PostStatusEnum.PUBLISHED
        post.external_post_id = external_post_id
        db.commit()
        logger.info("Published post %s successfully", post_id)
        notify_user(str(post.user_id), "Your post has been published.")
    finally:
        db.close()


@celery_app.task(name="backend.workers.tasks.enqueue_upcoming_posts_task")
def enqueue_upcoming_posts_task():
    """
    For posts scheduled > 24 hours, Celery Beat + this task will enqueue those
    in next 20 minutes into publish_post_task.
    """
    db = _get_db()
    try:
        now = datetime.now(timezone.utc)
        window_end = now + timedelta(minutes=20)
        posts = (
            db.query(Post)
            .filter(
                Post.status == PostStatusEnum.SCHEDULED,
                Post.scheduled_time >= now,
                Post.scheduled_time <= window_end,
            )
            .all()
        )
        for post in posts:
            logger.info("Enqueueing post %s for publish at %s", post.id, post.scheduled_time)
            publish_post_task.apply_async(args=[str(post.id)], eta=post.scheduled_time)
    finally:
        db.close()
