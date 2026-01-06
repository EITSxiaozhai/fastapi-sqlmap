from app.middleware.celery_app import celery_app

celery_app.conf.beat_schedule = {
    "poll-sqlmap-tasks-every-5-seconds": {
        "task": "app.tasks.sqlmap_scheduler.poll_active_sqlmap_tasks",
        "schedule": 5.0,
    }
}
