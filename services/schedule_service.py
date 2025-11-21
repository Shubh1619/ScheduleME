# backend/services/schedule_service.py

from datetime import datetime, timedelta, timezone

from backend.workers.tasks import publish_post_task, enqueue_upcoming_posts_task


def schedule_post_task(post_id: str, scheduled_time: datetime):
    """
    If < 24 hours away → schedule ETA task.
    Otherwise, Celery Beat polling will handle.
    """
    now = datetime.now(timezone.utc)
    delta = scheduled_time - now
    if delta <= timedelta(hours=24):
        publish_post_task.apply_async(args=[post_id], eta=scheduled_time)


def trigger_upcoming_scan():
    """
    Called by Celery Beat periodically to push posts for next 20 minutes.
    """
    enqueue_upcoming_posts_task.delay()
