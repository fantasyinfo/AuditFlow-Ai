from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "auditflow_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)

# Register worker tasks
import app.worker.tasks  # noqa: F401, E402


@celery_app.task(name="app.worker.tasks.ping")
def ping_task() -> str:
    """Simple ping task to verify worker health."""
    return "pong"
