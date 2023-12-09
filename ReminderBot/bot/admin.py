from django.contrib import admin
from .models import Account, Chat, ChatUser, Task

# Register your models here.

admin.site.register(Account)
admin.site.register(Chat)
admin.site.register(ChatUser)
admin.site.register(Task)
