import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Create Celery app
celery_app = Celery(__name__)

# Configure Celery with SQLite broker and result backend
broker_url = os.getenv("CELERY_BROKER_URL", "sqla+sqlite:///data/celery_broker.db")
result_backend = os.getenv(
    "CELERY_RESULT_BACKEND", "db+sqlite:///data/celery_results.db"
)

celery_app.conf.update(
    broker_url=broker_url,
    result_backend=result_backend,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=int(os.getenv("CELERY_WORKER_CONCURRENCY", "1")),
    task_time_limit=int(os.getenv("CELERY_TASK_TIME_LIMIT", "300")),
    result_expires=int(os.getenv("CELERY_RESULT_EXPIRES", "86400")),
)

# Import tasks to register them with Celery
from anki_sync_server.tasks import card_creation_task  # noqa: E402, F401
