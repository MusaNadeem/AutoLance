"""Alert-related Celery tasks.

This module exists because the Celery app is configured to include
`app.workers.alert_tasks`.

The full alerting workflow can be implemented here; for now, we provide a
minimal task to keep worker/beat/flower startup healthy.
"""

from celery import shared_task


@shared_task(name="app.workers.alert_tasks.noop")
def noop() -> str:
    return "ok"
