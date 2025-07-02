import requests
import os

from celery import shared_task

host = os.getenv('FLASK_HOST', 'localhost')
port = os.getenv('FLASK_PORT', '5005')

@shared_task
def send_reminder(user, task):
    url = f"http://{host}:{port}/send_remind"
    requests.post(url, json={'user': user, 'task': task})