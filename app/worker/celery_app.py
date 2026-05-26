import os

from celery import Celery

celery_app = Celery("seiton_brain", include=["app.worker.tasks"])
celery_app.conf.broker_url = os.environ["REDIS_URL"]
celery_app.conf.result_backend = os.environ["REDIS_URL"]
celery_app.conf.task_track_started = True
