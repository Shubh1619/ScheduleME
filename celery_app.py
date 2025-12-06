# backend/celery_app.py

from celery import Celery
from backend.config import get_settings

settings = get_settings()

celery_app = Celery(
    "schedulme",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.timezone = "UTC"
celery_app.conf.enable_utc = True

celery_app.conf.beat_schedule = {
    "enqueue-upcoming-posts-every-15-min": {
        "task": "backend.workers.tasks.enqueue_upcoming_posts_task",
        "schedule": 60 * 15,  # 15 minutes
    }
}
