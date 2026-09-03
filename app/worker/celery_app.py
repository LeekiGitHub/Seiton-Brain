from celery import Celery
from celery.signals import setup_logging, task_postrun, task_prerun

from app.config import settings
from app.licensing.startup import enforce_license_if_required
from app.logging_config import bind_log_context, clear_log_context, configure_logging

enforce_license_if_required()

celery_app = Celery("seiton_brain", include=["app.worker.tasks"])
celery_app.conf.broker_url = settings.redis_url
celery_app.conf.result_backend = settings.redis_url
celery_app.conf.task_track_started = True

# Celery Beat (E28-1): periodic vault index sync. Interval 0 = off.
_sync_interval = settings.seiton_index_sync_interval_seconds
if _sync_interval > 0:
    celery_app.conf.beat_schedule = {
        "sync-vault-index-incremental": {
            "task": "sync_vault_index_incremental",
            "schedule": float(_sync_interval),
        },
    }
celery_app.conf.timezone = "UTC"


@setup_logging.connect
def _configure_celery_logging(**_kwargs) -> None:
    configure_logging()


@task_prerun.connect
def _bind_task_id(task_id=None, **_kwargs) -> None:
    if task_id is not None:
        bind_log_context(task_id=task_id)


@task_postrun.connect
def _clear_task_context(**_kwargs) -> None:
    clear_log_context()
