import os
import django
import random
import datetime
import pytz
import requests
import json

from timezonefinder import TimezoneFinder

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ReminderBot.settings')
django.setup()

# from bot.models import Task, Chat
from django.contrib.auth import get_user_model
User = get_user_model()

#Exceptions
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


#request

#Base URL
BASE = "http://localhost:8000/api"

#user
def request_user(field, value):
    user = requests.get(f"{BASE}/user/{field}={value}").json()[0]
    return user


def request_user_create(firstname, username, telegram_id):
    url = f"{BASE}/users/"
    body = {
        'firstname': firstname,
        'username': username,
        'telegram_id': telegram_id,
        'password': generate_code()
    }
    request = requests.post(url, body)
    return request.json()

def request_user_update(id, field, value):
    url = f"{BASE}/users/{id}"
    body = {
        field: value
    }
    request = requests.patch(url, body)
    return request.json()

#Task
def request_task(field, value):
    tasks = requests.get(f"{BASE}/tasks/{field}={value}&complete=0&canceled=0").json()
    return tasks


def request_tasks_create(header, description, date, telegram_id):
    url = f"{BASE}/tasks/"
    user = request_user('telegram_id', telegram_id)
    body = {
        'header': header,
        'description': description,
        'date': date,
        'user': user['id'],
        'password': generate_code()
    }
    request = requests.post(url, body)
    return request.json()

#Functions

#Check and convert date and time to correct datetime object
#datetime_str - str format %d.%m.%Y %H:%M
def validate_datetime(datetime_str: str) -> datetime:
        try:
            date_time = datetime.datetime.strptime(datetime_str, '%d.%m.%Y %H:%M')
        except Exception:
            raise IncorrectFormat
        else:
            now = datetime.datetime.now()
            if now > date_time:
                raise TimePassed(f'{date_time} - это время уже прошло')
            else:
                return date_time


#Convert user local datetime to UTC
#datetime_dt: datetime - user local datetime object
#timezone: str - user timezone string (example 'Asia/Yekaterinburg')
def convert_to_utc(datetime_dt: datetime, timezone: str) -> datetime:
    user_tz = pytz.timezone(timezone)
    user_datetime = user_tz.localize(datetime_dt)
    utc_datetime = user_datetime.astimezone(pytz.UTC)
    return utc_datetime


def convert_to_user_tz(datetime_dt: datetime, telegram_id: int) -> datetime:
    timezone = request_user('telegram_id', telegram_id)['timezone']
    user_datetime = datetime_dt.astimezone(pytz.timezone(timezone))
    return user_datetime


def get_timezone_by_location(latitude, longitude):
    tf = TimezoneFinder()
    time_zone_str = tf.timezone_at(lat=latitude, lng=longitude)
    return time_zone_str


def generate_code():
    chars = '1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    password = ''
    for i in range(6):
        position = random.randint(0, 35)
        password += chars[position]
    return password

#ORM+ Functions
def add_new_user(firstname, username, telegram_id):
    if user_exist(telegram_id):
        raise UserAlreadyExist
    else:
        password = generate_code()
        request_user_create(firstname=firstname, username=username, telegram_id=telegram_id)
        return password


def update_user_tz(timezone: str, telegram_id: str):
    user = request_user('telegram_id', telegram_id)
    user.timezone = timezone
    user.save()


def user_exist(telegram_id):
    if request_user('telegram_id', telegram_id):
        return True


def new_password(telegram_id):
    user = request_user('telegram_id', telegram_id)
    password = generate_code()
    request_user_update(user['id'], "password", password)


def new_task(header, description, date, telegram_id):
    user = request_user('telegram_id', telegram_id)
    date_utc = convert_to_utc(date, user.timezone)
    request_tasks_create(header=header, description=description, date=date_utc, telegram_id=telegram_id)


def get_tasks(telegram_id):
    tasks = request_task('telegram_id', telegram_id)
    user = request_user('telegram_id', telegram_id)
    tasks_list = []
    for task in tasks:
        t = {}
        t['header'] = task['header']
        t['description'] = task['description']
        date = task['date'].astimezone(user['timezone'])
        t['date'] = date
        t['id'] = task['id']
        tasks_list.append(t)
    return tasks_list


#TODO Закончить функцию
def edit_task(task_id, field, value):
    task = request_task('id', task_id)
    user = request_user('id',task['user'])
    if field != "canceled":
        if field != 'date':
            setattr(task, field, value)
            task.save()
        else:
            date_obj = validate_datetime(value)
            date_utc = convert_to_utc(date_obj, user.timezone)
            task.date = date_utc
            task.save()
    else:
        setattr(task, field, 1)
        task.save()

#Testing
if __name__ == '__main__':
    datetime_test = Task.objects.get(id=2).date
    tz = User.objects.get(id=3).timezone
    print(convert_to_user_tz(datetime_test, tz))
    # edit_task(2, "header", 'Совещание с лягушками')
    #print(get_tasks(268699254))
    # print(convert_to_utc(datetime.datetime.now(), 'Asia/Yekaterinburg'))
    # add_new_user("test", "test2")
    # a = get_account('sa1nttony')
    # print(a['username'], a['password'])
    # new_password(a['username'])
    # b = get_account('sa1nttony')
    # print(b['username'], b['password'])
    # add_new_user('anton', 'antonius7')
    # task = Task()
    # task.get_date = '01 09 2023'
    # task.get_time = '00:40'
    # print(task.get_time)
    # print(task.get_date)