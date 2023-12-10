import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ReminderBot.settings')
django.setup()

from bot.models import Account, User

Account.objects.create(user=User.objects.get(pk=1), firstname='test', username='test')