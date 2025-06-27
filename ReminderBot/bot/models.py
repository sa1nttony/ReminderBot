from celery.result import AsyncResult

from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.views.decorators.http import condition
from django_lifecycle import hook, AFTER_CREATE, AFTER_UPDATE, LifecycleModelMixin
from django_lifecycle.conditions import WhenFieldHasChanged

from .tasks import send_reminder


# Create your models here.

class User(AbstractUser):
    timezone = models.CharField(max_length=63, default='UTC', verbose_name='Часовой пояс')
    telegram_id = models.CharField(max_length=256)

class Chat(models.Model):
    chat_id = models.CharField(max_length=256)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='ChatUser')


class ChatUser(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Task(LifecycleModelMixin, models.Model):
    header = models.CharField(max_length=256)
    description = models.TextField()
    date = models.DateTimeField()
    complete = models.BooleanField(default=False)
    canceled = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, null=True)
    celery_task = models.CharField(max_length=128, null=True, blank=True)

    @hook(AFTER_CREATE)
    def create_scheduler(self):
        res = send_reminder.apply_async(
            args=[self.user, self],
            eta=self.date
        )
        self.celery_task = res.id
        self.save(update_fields=['celery_task'])

    @hook(AFTER_UPDATE, condition=WhenFieldHasChanged('date', has_changed=True))
    def update_scheduler(self):
        if self.celery_task:
            AsyncResult(self.celery_task).revoke()
        res = send_reminder.apply_async(
            args=[self.user, self],
            eta=self.date
        )
        self.celery_task = res.id
        self.save(update_fields=['celery_task'])

    @hook(AFTER_UPDATE, condition=(WhenFieldHasChanged('canceled', has_changed=True) or WhenFieldHasChanged('complete', has_changed=True)))
    def delete_scheduler(self):
        if self.celery_task:
            AsyncResult(self.celery_task).revoke()
        self.celery_task = ''
        self.save(update_fields=['celery_task'])