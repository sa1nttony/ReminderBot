import telebot
import datetime
import random
import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ReminderBot.settings')
django.setup()

from config import TOKEN
from phrases import commands, example_headers, example_descriptions, hints
from bot.models import Chat, ChatUser, Task, User
from utils import (IncorrectFormat,
                   TimePassed,
                   UserAlreadyExist,
                   add_new_user,
                   user_exist,
                   get_account,
                   new_password,
                   new_task,
                   validate_datetime,
                   get_timezone_by_location,
                   update_user_tz,
                   edit_task,
                   get_tasks
                   )


tbot = telebot.TeleBot(TOKEN, threaded=True, num_threads=300, parse_mode='HTML')

#TODO Добавление чата в бд при добавлении бота, добавления юзера в список пользователей чата, при добавлении его в чат, исправить функцию new_task
@tbot.message_handler(commands=['help'])
def info(message: telebot.types.Message):
    text = 'Цель данного бота - напоминать о важных событиях \n \n' \
    'В личных сообщениях можно задавать напоминания для себя, а в групповых чатах оставлять задания ' \
    'и напоминания для коллег, друзей или единомышленников \n \n' \
    'Доступные комманды: \n'
    counter = 1
    for c in [*commands]:
        cmnd = f'{counter}. {c} - {commands[c]}\n'
        text = text + cmnd
        counter += 1
    tbot.reply_to(message, text)


@tbot.message_handler(commands=['start'])
def register_user(message: telebot.types.Message):
    firstname = message.from_user.first_name
    username = message.from_user.username
    telegram_id = message.from_user.id
    try:
        password = add_new_user(firstname, username, telegram_id)
    except UserAlreadyExist as e:
        tbot.reply_to(message, f'Ошибка: {e}')
    else:
        self_message = f"""Вы успешно зарегистрированы! \nВаш логин <strong>{username}</strong> 
        Ваш пароль <span class="tg-spoiler"><strong>{password}</strong></span>"""
        tbot.reply_to(message, self_message, parse_mode='HTML')
        get_user_tz(message)


def get_user_tz(message):
    text = """Для того, чтобы напоминания были актуальны по времени, отправь мне свою геопозицию. 🌍
Благодаря ней я смогу вычислить твой часовой пояс"""
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button = telebot.types.KeyboardButton('Отправить местоположение', request_location=True)
    markup.add(button)
    tbot.send_message(message.chat.id, text, reply_markup=markup)


@tbot.message_handler(commands=['tz'])
def change_user_tz(message: telebot.types.Message):
    user_tz = User.objects.get(telegram_id=message.from_user.id).timezone
    text = f"Твой текущий часовой пояс - {user_tz}"
    tbot.send_message(message.chat.id, text)
    get_user_tz(message)


@tbot.message_handler(commands=['my_account'])
def my_account(message: telebot.types.Message):
    username = message.from_user.username
    user_id = message.from_user.id
    chat_id = message.chat.id
    account = get_account(username)
    if user_id != chat_id:
        tbot.reply_to(message, f'Эту команду лучше написать мне в личные сообщения @{tbot.user.username}, '
                               f'ты ведь не хочешь, чтобы весь чат увидел твои логин и пароль?')
    else:
        tbot.reply_to(message, f"""Ваш логин <strong>{account['username']}</strong>\nВаш пароль <span class="tg-spoiler"><strong>{account['password']}</strong></span>""",
                      parse_mode='HTML')


@tbot.message_handler(commands=['change_password'])
def change_password(message: telebot.types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if user_id != chat_id:
        tbot.reply_to(message, f'Эту команду лучше написать мне в личные сообщения @{tbot.user.username}, '
                               f'ты ведь не хочешь, чтобы весь чат увидел твой новый пароль?')
    else:
        new_password(user_id)
        account = get_account(user_id)
        tbot.reply_to(message, f"""Пароль успешно изменен\nВаш логин <strong>{account['username']}</strong>\nВаш пароль <span class="tg-spoiler"><strong>{account['password']}</strong></span>""",
                      parse_mode='HTML')

#Вычисление tz
@tbot.message_handler(content_types=['location'])
def get_location(message: telebot.types.Message):
    latitude = message.location.latitude
    longitude = message.location.longitude
    tz = get_timezone_by_location(longitude=longitude, latitude=latitude)
    update_user_tz(tz, str(message.from_user.id))
    text = f"Твой часовой пояс - {str(tz)}"
    markup = telebot.types.ReplyKeyboardRemove()
    tbot.send_message(message.chat.id, text, reply_markup=markup)


#Блок создания задания
@tbot.message_handler(commands=['new_task'])
def start_task(message: telebot.types.Message):
    telegram_id = message.from_user.id
    task_info = {}
    task_info['chat'] = message.chat.id
    task_info['user'] = telegram_id
    msg = tbot.send_message(message.chat.id, f'Начинаем создание нового задания для @{task_info["user"]}\n'
                                     f'Укажите короткое описание события. Например "{example_headers[random.randint(0, len(example_headers)-1)]}"')
    task_info['prev_msg'] = (msg.chat.id, msg.id)
    tbot.register_next_step_handler(message, task_header, task_info)


def task_user(message, task_info):
    task_info['user'] = message.text[1::]
    tbot.delete_message(message.chat.id, message.id)
    tbot.delete_message(message.chat.id, message.id - 1)
    msg = tbot.send_message(message.chat.id, f'Начинаем создание нового задания для @{task_info["user"]}\n'
                                             f'Укажите короткое описание события. Например "{example_headers[random.randint(0, len(example_headers) - 1)]}"')
    tbot.register_next_step_handler(msg, task_header, task_info)


def task_header(message, task_info):
    task_info['header'] = message.text
    tbot.delete_message(message.chat.id, message.id)
    message_text = f"""<strong>💡 Создание новой задачи:</strong>

<strong>Название</strong>: <em>{task_info['header']}</em>
_____
Теперь укажите более подробное описание события. Например "{example_descriptions[random.randint(0, len(example_headers)-1)]}\""""
    tbot.edit_message_text(message_text, task_info['prev_msg'][0], task_info['prev_msg'][1])
    tbot.register_next_step_handler(message, task_datetime, task_info)


def task_datetime(message, task_info):
    task_info['description'] = message.text
    tbot.delete_message(message.chat.id, message.id)
    message_text = f"""<strong>💡 Создание новой задачи:</strong>

<strong>Название</strong>: <em>{task_info['header']}</em>
<strong>Описание</strong>: <em>{task_info['description']}</em>
_____
Теперь укажите дату события в формате "ДД ММ ГГГГ ЧЧ:ММ". Например "{datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}\""""
    tbot.edit_message_text(message_text, task_info['prev_msg'][0], task_info['prev_msg'][1])
    tbot.register_next_step_handler(message, create_task, task_info)


def create_task(message, task_info):
    try:
        tbot.delete_message(message.chat.id, message.id)
        date = validate_datetime(message.text)
    except (IncorrectFormat, TimePassed) as error:
        error_text = f"""<strong>💡 Создание новой задачи:</strong>

<strong>Название</strong>: <em>{task_info['header']}</em>
<strong>Описание</strong>: <em>{task_info['description']}</em>
_____
❌ Ошибка
{error}
Укажите дату события в формате "ДД.ММ.ГГГГ ЧЧ:ММ". Например "{datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}\""""
        tbot.edit_message_text(error_text, task_info['prev_msg'][0], task_info['prev_msg'][1])
        tbot.register_next_step_handler(message, create_task, task_info)
    else:
        task_info['date'] = date
        message_text = f"""<strong>✅Новая задача создана:</strong>

<strong>Название</strong>: <em>{task_info['header']}</em>
<strong>Описание</strong>: <em>{task_info['description']}</em>
<strong>Дата и время</strong>: <em>{task_info['date']}</em>
    """
        tbot.edit_message_text(message_text, task_info['prev_msg'][0], task_info['prev_msg'][1])
        new_task(task_info['header'], task_info['description'], task_info['date'], task_info['user'])


#Блок изменения напоминаний
def send_tasks(telegram_id, chat_id):
    markup = telebot.types.InlineKeyboardMarkup()
    tasks = get_tasks(telegram_id)
    for task in tasks:
        button = telebot.types.InlineKeyboardButton(text=task['header'], callback_data=f"show_task:{task['id']}")
        markup.add(button)
    tbot.send_message(chat_id, "Выбери напоминание:", reply_markup=markup)


@tbot.message_handler(commands=['show_tasks'])
def show_tasks(message: telebot.types.Message):
    send_tasks(message.from_user.id, message.chat.id)


#Callback handler
@tbot.callback_query_handler(func=lambda call: call.data.startswith("show_task:"))
def task_details(call):
    task_id = call.data.split(":")[1]
    message_id = call.message.message_id
    telegram_id = call.from_user.id
    markup = telebot.types.InlineKeyboardMarkup()
    task = Task.objects.get(id=task_id)
    markup.add(telebot.types.InlineKeyboardButton(text="📜 Изменить название", callback_data=f"edit_task:{task_id}:header"))
    markup.add(telebot.types.InlineKeyboardButton(text="✏️ Изменить описание", callback_data=f"edit_task:{task_id}:description"))
    markup.add(telebot.types.InlineKeyboardButton(text="📅 Изменить дату и время", callback_data=f"edit_task:{task_id}:date"))
    markup.add(telebot.types.InlineKeyboardButton(text="❌ Удалить напоминание", callback_data=f"edit_task:{task_id}:complete"))
    markup.add(telebot.types.InlineKeyboardButton(text="<< Назад к списку", callback_data=f"back"))
    text = f"""<strong>🗓 Предстоящее событие:</strong>
<strong>Название</strong>: <em>{task.header}</em>
<strong>Описание</strong>: <em>{task.description}</em>
<strong>Дата и время</strong>: <em>{task.date}</em>"""
    tbot.edit_message_text(chat_id=telegram_id, message_id=message_id, text=text, reply_markup=markup)

@tbot.callback_query_handler(func=lambda call: call.data.startswith("back"))
def back_to_tasks(call):
    tbot.delete_message(call.message.chat.id, call.message.message_id)
    send_tasks(call.from_user.id, call.message.chat.id)

######
######
#FIXME сделать отдельный вариант для отмены задания, чтобы не пришлось ничего воодить пользователю
#####
#####
#####
@tbot.callback_query_handler(func=lambda call: call.data.startswith("edit_task:"))
def get_update_task_info(call):
    task_id = call.data.split(":")[1]
    field = call.data.split(":")[2]
    task = Task.objects.get(id=task_id)
    text = f"""<strong>📝 Изменение события:</strong>
    <strong>Название</strong>: <em>{task.header}</em>
    <strong>Описание</strong>: <em>{task.description}</em>
    <strong>Дата и время</strong>: <em>{task.date}</em>
_________________
Отправьте новое значение:"""
    tbot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=text, reply_markup=None)
    tbot.register_next_step_handler(call.message, update_task, task_id, field, call.message)

def update_task(message, task_id, field, bot_message):
    edit_task(task_id, field, message.text)
    task = Task.objects.get(id=task_id)
    tbot.delete_message(message.chat.id, message.id)
    text = f"""<strong>⭐️ Изменения внесены:</strong>
<strong>Название</strong>: <em>{task.header}</em>
<strong>Описание</strong>: <em>{task.description}</em>
<strong>Дата и время</strong>: <em>{task.date}</em>"""
    tbot.edit_message_text(chat_id=bot_message.chat.id, message_id=bot_message.id, text=text)

#TODO Написать функцию для отправки уведомления
def send_remind():
    pass

# Работа бота нонстопом, даже при ошибках
while True:
    try:
        tbot.polling(none_stop=True)
    except Exception as e:
        print(f"Ошибка polling: {e}")
        time.sleep(1)
