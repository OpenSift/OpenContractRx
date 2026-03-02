import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "opencontractrx_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.autodiscover_tasks(["opencontractrx_worker.tasks"])

if __name__ == "__main__":
    # Run a worker when executed as a module.
    # Compose uses this entrypoint.
    celery_app.worker_main(["worker", "--loglevel=INFO"])