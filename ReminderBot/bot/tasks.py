from celery import shared_task

from models import User, Task

@shared_task
def send_reminder(user_id, task_id):
    pass