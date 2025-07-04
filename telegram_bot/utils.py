import os
import django
import random
import datetime
import pytz
import requests
import json

from timezonefinder import TimezoneFinder

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
host = os.getenv('DJANGO_HOST', 'localhost')
port = os.getenv('DJANGO_PORT', '8000')

BASE = f"http://{host}:{port}/api"

#user
def request_user(field, value):
    user = requests.get(f"{BASE}/users/?{field}={value}").json()[0]
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
    tasks = requests.get(f"{BASE}/tasks/?{field}={value}&complete=0&canceled=0").json()
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


def request_tasks_update(id, field, value):
    url = f"{BASE}/tasks/{id}"
    body = {
        field: value
    }
    response = requests.patch(url, json=body)
    return response.json()

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

def convert_datetime_for_request(datetime_obj: datetime):
    date_time_str = datetime.datetime.strftime(datetime_obj, '%Y-%m-%dT%H:%M:%SZ')
    return date_time_str

def convert_datetime_for_obj(datetime_str: str):
    date_time_obj = datetime.datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%SZ')
    return date_time_obj

#Convert user local datetime to UTC
#datetime_dt: datetime - user local datetime object
#timezone: str - user timezone string (example 'Asia/Yekaterinburg')
def convert_to_utc(datetime_dt: datetime, timezone: str) -> datetime:
    user_tz = pytz.timezone(timezone)
    user_datetime = user_tz.localize(datetime_dt)
    utc_datetime = user_datetime.astimezone(pytz.UTC)
    return utc_datetime


def convert_to_user_tz(datetime_dt: datetime, telegram_id: int, entry_timezone_utc=True) -> datetime:
    timezone = request_user('telegram_id', telegram_id)['timezone']
    entry_timezone = 'UTC' if entry_timezone_utc else timezone
    user_datetime = convert_to_utc(datetime_dt, entry_timezone).astimezone(pytz.timezone(timezone))
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
        user = request_user_create(firstname=firstname, username=username, telegram_id=telegram_id)
        request_user_update(user['id'], 'password', password)
        return password


def update_user_tz(timezone: str, telegram_id: str):
    user = request_user('telegram_id', telegram_id)
    request_user_update(user['id'], 'timezone', timezone)


def user_exist(telegram_id):
    try:
        user = request_user('telegram_id', telegram_id)
    except Exception as e:
        return False
    else:
        if user:
            return True
        else:
            return False


def new_password(telegram_id):
    user = request_user('telegram_id', telegram_id)
    password = generate_code()
    request_user_update(user['id'], "password", password)


def new_task(header, description, date, telegram_id):
    print(header, description, date, telegram_id)
    user = request_user('telegram_id', telegram_id)
    date_utc = convert_to_utc(date, user['timezone'])
    request_tasks_create(header=header, description=description, date=date_utc, telegram_id=telegram_id)


def get_tasks(telegram_id):
    user = request_user('telegram_id', telegram_id)
    tasks = request_task('user_id', user['id'])
    tasks_list = []
    for task in tasks:
        t = {}
        t['header'] = task['header']
        t['description'] = task['description']
        date = convert_datetime_for_obj(task['date']).astimezone(pytz.timezone(user['timezone']))
        t['date'] = date
        t['id'] = task['id']
        tasks_list.append(t)
    return tasks_list


def edit_task(task_id, field, value):
    task = request_task('id', task_id)[0]
    user = request_user('id',task['user'])
    if field != "canceled":
        if field != 'date':
            request_tasks_update(task_id, field, value)
        else:
            date_obj = validate_datetime(value)
            date_utc = convert_to_utc(date_obj, user['timezone'])
            print(convert_datetime_for_request(date_utc))
            request_tasks_update(task_id, field, convert_datetime_for_request(date_utc))
    else:
        request_tasks_update(task_id, field, 1)

#Testing
if __name__ == '__main__':
    # date = convert_datetime_for_obj('2025-06-27T13:40:00Z')
    # print(convert_to_user_tz(date, 268699254).strftime('%d.%m.%Y %H:%M'))
    # print(request_tasks_update(3, 'date', '2025-07-27T13:40:00Z'))
    print(edit_task(3, 'date', '04.07.2025 04:28'))
    # datetime_test = Task.objects.get(id=2).date
    # tz = User.objects.get(id=3).timezone
    # print(convert_to_user_tz(datetime_test, tz))
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