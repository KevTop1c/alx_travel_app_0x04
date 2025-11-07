import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_travel_app.settings")

app = Celery("alx_travel_app")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


# Celery Beat schedule for periodic tasks (optional)
app.conf.beat_schedule = {
    "check-pending-payments-every-hour": {
        "task": "core.tasks.check_pending_payments",
        "schedule": 3600.0,  # Every hour (in seconds)
    },
}

# Timezone
app.conf.timezone = "UTC"
