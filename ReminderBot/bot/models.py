from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django_lifecycle import hook, AFTER_CREATE, AFTER_UPDATE, LifecycleModelMixin

# Create your models here.

class User(AbstractUser):
    timezone = models.CharField(max_length=63, default='UTC', verbose_name='Часовой пояс')
    telegram_id = models.CharField(max_length=256)

class Chat(models.Model):
    chat_id = models.CharField(max_length=256)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='ChatUser')

#
class ChatUser(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Task(models.Model):
    header = models.CharField(max_length=256)
    description = models.TextField()
    date = models.DateTimeField()
    complete = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, null=True)
