from django.db import models
from django.contrib.auth.models import User
from django_lifecycle import hook, AFTER_CREATE, AFTER_UPDATE, LifecycleModelMixin

# Create your models here.


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=128)
    username = models.CharField(max_length=128)


class Chat(models.Model):
    chat_id = models.CharField(max_length=256)
    users = models.ManyToManyField(Account, through='ChatUser')


class ChatUser(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)


class Task(models.Model):
    header = models.CharField(max_length=256)
    description = models.TextField()
    date = models.DateTimeField()
    complete = models.BooleanField(default=False)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
