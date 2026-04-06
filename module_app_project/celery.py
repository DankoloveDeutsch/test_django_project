"""
Celery configuration for the HR System project.
Used for handling background tasks like sending reminders, syncing with 1C, etc.
"""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'module_app_project.settings')

app = Celery('module_app_project')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery connectivity"""
    print(f'Request: {self.request!r}')