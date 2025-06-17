import os
import django
import random
import datetime
import pytz
from timezonefinder import TimezoneFinder

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ReminderBot.settings')
django.setup()

from bot.models import Task, Chat
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
    if user_exist(username):
        raise UserAlreadyExist
    else:
        password = generate_code()
        user = User.objects.create(first_name=firstname, username=username, telegram_id=telegram_id)
        user.set_password(password)
        user.save()
        return password

def update_user_tz(timezone: str, telegram_id: str):
    user = User.objects.get(telegram_id=telegram_id)
    user.timezone = timezone
    user.save()


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


def new_task(header, description, date, username):
    user = User.objects.get(username=username)
    Task.objects.create(header=header, description=description, date=date, user=user)


#Testing
if __name__ == '__main__':
    add_new_user("test", "test2")
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