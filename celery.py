from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coffee_machine_controller.settings')

app = Celery('coffee_machine_controller')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Schedule periodic tasks
from celery.schedules import crontab

app.conf.beat_schedule = {
    'health-check-every-5-minutes': {
        'task': 'machine.tasks.health_check_task',
        'schedule': crontab(minute='*/5'),
    },
}

app.conf.timezone = 'UTC'