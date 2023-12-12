import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ReminderBot.settings')
django.setup()

from bot.models import User, Task


class ReminderBotException(Exception):
    pass


class UserAlreadyExist(ReminderBotException):
    def __str__(self):
        return 'Этот пользователь уже зарегистрирован в базе данных'


class FakeDate(ReminderBotException):
    def __str__(self):
        return 'Такой даты не существует'


class TimePassed(ReminderBotException):
    def __str__(self):
        return 'Указанные время и дата уже прошли'


class IncorrectFormat(ReminderBotException):
    def __str__(self):
        return "Данные введены в некорректном формате"


# class Task:
#     def __init__(self):
#         self.header = None
#         self.description = None
#         self.date = None
#         self.time = None
#         self.complete = 0
#         self.user_id = None
#         self.creator_id = None
#
#     def __str__(self):
#         return f'{self.header}: \n{self.description} \nЗапланировано: \n{self.date + " " + self.time}'
#
#     @property
#     def get_header(self):
#         return self.header
#
#     @get_header.setter
#     def get_header(self, header):
#         self.header = header
#
#     @property
#     def get_description(self):
#         return self.description
#
#     @get_description.setter
#     def get_description(self, description):
#         self.description = description
#
#     @property
#     def get_date(self):
#         return self.date
#
#     @get_date.setter
#     def get_date(self, date):
#         try:
#             request_date = datetime.datetime.strptime(date, '%d %m %Y').date()
#         except Exception:
#             raise FakeDate
#         else:
#             now = datetime.datetime.now().date()
#             if now > request_date:
#                 raise TimePassed(f'{date} - эта дата уже прошла')
#             else:
#                 self.date = date
#
#     @property
#     def get_time(self):
#         return self.time
#
#     @get_time.setter
#     def get_time(self, time):
#         request_date_time = self.date + ' ' + time
#         try:
#             date_time = datetime.datetime.strptime(request_date_time, '%d %m %Y %H:%M')
#         except Exception:
#             raise IncorrectFormat
#         else:
#             now = datetime.datetime.now()
#             if now > date_time:
#                 raise TimePassed(f'{date_time} - это время уже прошло')
#             else:
#                 self.time = time
#
#     @property
#     def get_user_id(self):
#         return self.user_id
#
#     @get_user_id.setter
#     def get_user_id(self, user_id):
#         self.user_id = user_id    \
#
#     @property
#     def get_creator_id(self):
#         return self.creator_id
#
#     @get_creator_id.setter
#     def get_creator_id(self, creator_id):
#         self.creator_id = creator_id
#
#     def completed(self):
#         self.complete = 1
#
#     def db_export(self):
#         new_task(self.header, self.description, self.date, self.time, self.complete, self.user_id, self.creator_id)


def add_new_user(firstname, username):
    if user_exist(username):
        raise UserAlreadyExist
    else:
        password = generate_code()
        User.objects.create(first_name=firstname, username=username, password=password)


def user_exist(username):
    if User.objects.filter(username=username):
        return True


def get_account(username):
    user = User.objects.filter(username=username).values('username', 'password')[0]
    account = {'username': user['username'], 'password': user['password']}
    return account


def new_password(username):
    user = User.objects.get(username=username)
    user.password = generate_code()
    user.save()


def generate_code():
    chars = '1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    password = ''
    for i in range(6):
        position = random.randint(0, 35)
        password += chars[position]
    return password


def new_task(header, description, date, user, chat):
    Task.objects.create(header=header, description=description, date=date, user=user, chat=chat)


if __name__ == '__main__':
    a = get_account('sa1nttony')
    print(a['username'], a['password'])
    new_password(a['username'])
    b = get_account('sa1nttony')
    print(b['username'], b['password'])
    # add_new_user('anton', 'antonius7')
    # task = Task()
    # task.get_date = '01 09 2023'
    # task.get_time = '00:40'
    # print(task.get_time)
    # print(task.get_date)