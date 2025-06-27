from celery import shared_task


from ReminderBot.app import send_remind

@shared_task
def send_reminder(user, task):
    send_remind(task, user)