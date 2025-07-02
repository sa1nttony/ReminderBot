import requests
from celery import shared_task

@shared_task
def send_reminder(user, task):
    url = "http://localhost:5005/send_remind"
    requests.post(url, json={'user': user, 'task': task})