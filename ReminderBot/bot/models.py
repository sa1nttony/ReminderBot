import datetime
import json
import uuid

from celery.result import AsyncResult

from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.views.decorators.http import condition
from django_lifecycle import hook, AFTER_CREATE, AFTER_UPDATE, LifecycleModelMixin
from django_lifecycle.conditions import WhenFieldHasChanged
from django_celery_beat.models import PeriodicTask, CrontabSchedule, ClockedSchedule
from .tasks import send_reminder


# Create your models here.

class User(LifecycleModelMixin, AbstractUser):
    timezone = models.CharField(max_length=63, default='UTC', verbose_name='Часовой пояс')
    telegram_id = models.CharField(max_length=256)

    # @hook(AFTER_CREATE)
    # def encode_password(self):
    #     password = self.password
    #     self.set_password(password)
    #     self.save(update_fields=['password'])

    @hook(AFTER_UPDATE, condition=WhenFieldHasChanged('password', has_changed=True))
    def encode_password(self):
        if len(self.password) == 6:
            password = self.password
            self.set_password(password)
            self.save(update_fields=['password'])


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
    periodic_task = models.OneToOneField(PeriodicTask, null=True, blank=True, on_delete=models.CASCADE, related_name='reminder_task')


    def create_beat_task(self):
        user = {
            'telegram_id': self.user.telegram_id
        }
        task = {
            'id': self.id,
            'header': self.header,
            'description': self.description,
            "date": datetime.datetime.strftime(self.date, '%Y-%m-%dT%H:%M:%SZ')
        }
        clocked, _ = ClockedSchedule.objects.get_or_create(clocked_time=self.date)
        periodic_task = PeriodicTask.objects.create(
            clocked=clocked,
            name=f"task-remind-{self.id}-uuid:{uuid.uuid4()}",
            task='bot.tasks.send_reminder',
            args=json.dumps([user, task]),
            one_off=True,
        )
        self.periodic_task = periodic_task
        self.save(update_fields=['periodic_task'])

#beat
    @hook(AFTER_CREATE)
    def create_scheduler(self):
        self.create_beat_task()

    @hook(AFTER_UPDATE, condition=(
            WhenFieldHasChanged('date', has_changed=True) |
            WhenFieldHasChanged("header", has_changed=True) |
            WhenFieldHasChanged("description", has_changed=True)
    ))
    def update_scheduler(self):
        if self.periodic_task:
            self.periodic_task.enabled = False
            self.periodic_task.save()
        self.create_beat_task()


    @hook(AFTER_UPDATE, condition=(
            WhenFieldHasChanged('canceled', has_changed=True) |
            WhenFieldHasChanged('complete', has_changed=True)))
    def delete_scheduler(self):
        periodic_task = self.periodic_task
        if periodic_task:
            periodic_task.enabled = False
            periodic_task.save()
        self.periodic_task = None
        self.save(update_fields=["periodic_task"])
