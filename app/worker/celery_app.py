from celery import Celery

from app.config import settings

celery_app = Celery("seiton_brain", include=["app.worker.tasks"])
celery_app.conf.broker_url = settings.redis_url
celery_app.conf.result_backend = settings.redis_url
celery_app.conf.task_track_started = True
