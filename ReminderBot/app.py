import telebot
import datetime
import random
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ReminderBot.settings')
django.setup()

from config import TOKEN
from phrases import commands, example_headers, example_descriptions, hints
from bot.models import Chat, ChatUser, Task
# from DB.handler_db import new_user, new_task, get_user_id, update_user
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
                   )


tbot = telebot.TeleBot(TOKEN, threaded=True, num_threads=300, parse_mode='HTML')

#TODO Добавление чата в бд при добавлении бота, добавления юзера в список пользователей чата, при добавлении его в чат, исправить функцию new_task
@tbot.message_handler(commands=['help'])
def info(message: telebot.types.Message):
    text = 'Цель данного бота - напоминать о важных событиях как одного человека, так и группы людей. \n \n' \
    'В личных сообщениях можно задавать напоминания для себя, а в групповых чатах оставлять задания ' \
    'и напоминания для коллег, друзей или единомышленников \n \n' \
    'Доступные комманды: \n'
    counter = 1
    for c in [*commands]:
        cmnd = f'{counter}. {c} - {commands[c]}\n'
        text = text + cmnd
        counter += 1
    tbot.reply_to(message, text)


# # @tbot.message_handler(content_types=['new_chat_members'])
# @tbot.message_handler(commands=['/init'])
# def register_member(message: telebot.types.Message):
#     firstname = message.json['new_chat_member']['first_name']
#     username = message.json['new_chat_member']['username']
#     user_id = message.json['new_chat_member']['id']
#     chat_id = message.chat.id
#     if user_id != tbot.user.id:
#         try:
#             add_new_user(firstname, username)
#         except UserAlreadyExist as e:
#             tbot.reply_to(message, f'Привет, @{username}! Мы с тобой уже знакомы. Если забыл пароль или логин - напиши мне в личные сообщения команду /my_account')
#         else:
#             tbot.reply_to(message,
#                          f'Пользователь @{username} успешно зарегистрирован. '
#                          f'Чтобы узнать логин и пароль - напиши мне в личные сообщения(@{tbot.user.username}) команду /my_account')
#     else:
#         tbot.send_message(chat_id, 'Привет! Я бот, созданный для того, чтобы напоминать о чем-либо. '
#                                    '\nОтправь команду /help, чтобы узнать больше о моих способностях')


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
    #TODO Добавить следующий шаг по добавлению таймзоны
    #TODO Добавить команду обновления таймзоны


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
    username = message.from_user.username
    user_id = message.from_user.id
    chat_id = message.chat.id
    if user_id != chat_id:
        tbot.reply_to(message, f'Эту команду лучше написать мне в личные сообщения @{tbot.user.username}, '
                               f'ты ведь не хочешь, чтобы весь чат увидел твой новый пароль?')
    else:
        new_password(username)
        account = get_account(username)
        tbot.reply_to(message, f"""Пароль успешно изменен\nВаш логин <strong>{account['username']}</strong>\nВаш пароль <span class="tg-spoiler"><strong>{account['password']}</strong></span>""",
                      parse_mode='HTML')

#Вычисление tz
@tbot.message_handler(content_types=['location'])
def get_location(message: telebot.types.Message):
    latitude = message.location.latitude
    longitude = message.location.longitude
    tz = get_timezone_by_location(longitude=longitude, latitude=latitude)
    update_user_tz(tz, str(message.from_user.id))


#Блок создания задания
@tbot.message_handler(commands=['new_task'])
def start_task(message: telebot.types.Message):
    username = message.from_user.username
    task_info = {'chat': message.chat.id}
    task_info['user'] = username
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
<strong>Дата и время</strong>: <em>{task_info['date']}</em>\n
    """
        tbot.edit_message_text(message_text, task_info['prev_msg'][0], task_info['prev_msg'][1])
        new_task(task_info['header'], task_info['description'], task_info['date'], task_info['user'])


# @bot.message_handler(commands=['admin'])
# def create_superuser(message: telebot.types.Message):
#     username = message.from_user.username
#     chat_id = message.chat.id
#     user_id = get_user_id(username, chat_id)[0][0]
#     update_user(user_id, 'is_superuser', 1)
#     text = f'{message.from_user.first_name} теперь может давать задания другим пользователям чата'
#     bot.reply_to(message, text)
#
#
# #Блок создания задания
# @bot.message_handler(commands=['new_task'])
# def start_new_task(message: telebot.types.Message):
#     start_message = message
#     task = Task()
#     msg = bot.send_message(message.chat.id,
#                            f'Укажите короткое описание события. Например "{example_headers[random.randint(0, len(example_headers)-1)]}"')
#     bot.register_next_step_handler(msg, task_header, task, start_message)
#
#
# def task_header(message, task, start_message):
#     task.get_header = message.text
#     msg = bot.send_message(message.chat.id,
#                            f'Укажите более подробное описание события. Например "{example_descriptions[random.randint(0, len(example_headers)-1)]}"')
#     bot.register_next_step_handler(msg, task_date, task, start_message)
#
#
# def task_date(message, task, start_message):
#     task.get_description = message.text
#     msg = bot.send_message(message.chat.id, f'Укажите дату события в формате "ДД ММ ГГГГ". Например "{datetime.date.today().strftime("%d %m %Y")}"')
#     bot.register_next_step_handler(msg, task_time, task, start_message)
#
#
# def task_time(message, task, start_message):
#     try:
#         task.get_date = message.text
#     except Exception as e:
#         msg = bot.send_message(message.chat.id,
#                                f'{e}\nУкажите дату события в формате "ДД ММ ГГГГ". Например "{datetime.date.today().strftime("%d %m %Y")}"')
#         bot.register_next_step_handler(msg, task_time, task, start_message)
#     else:
#         msg = bot.send_message(message.chat.id,
#                                f'Укажите время события в формате "ЧЧ:ММ". Например "{datetime.datetime.now().strftime("%H:%M")}"')
#         bot.register_next_step_handler(msg, task_user, task, start_message)
#
#
# def task_user(message, task, start_message):
#     try:
#         task.get_time = message.text
#     except Exception as e:
#         msg = bot.send_message(message.chat.id,
#                                f'{e}\nУкажите время события в формате "ЧЧ:ММ". Например "{datetime.datetime.now().strftime("%H:%M")}"')
#         bot.register_next_step_handler(msg, task_user, task, start_message)
#     else:
#         if user_exist(start_message.from_user.username, message.chat.id):
#             task.get_creator_id = get_user_id(start_message.from_user.username, message.chat.id)[0][0]
#             if start_message.from_user.id == message.chat.id:
#                 task.get_user_id = task.get_creator_id
#                 task_commit(start_message, task)
#             else:
#                 msg = bot.send_message(message.chat.id,
#                                        f'Укажите пользователя, для которого нужно назначить задание. Например @{start_message.from_user.username}')
#                 bot.register_next_step_handler(msg, task_commit, task)
#         else:
#             bot.send_message(message.chat.id, f'Пользователь {start_message.from_user.username} не был инициализирован. \n'
#                                               f'Для инициализации, пользователь должен отправить команду /init')
#
#
# def task_commit(message, task, attempt=0):
#     if not task.get_user_id:
#         if user_exist(message.text.replace('@', ''), message.chat.id):
#             task.get_user_id = get_user_id(message.text.replace('@', ''), message.chat.id)[0][0]
#             try:
#                 task.db_export()
#             except Exception as e:
#                 msg = f'{e}\n'
#                 for hint in hints:
#                     msg = msg + hint
#                 bot.send_message(message.chat.id, msg)
#             else:
#                 bot.send_message(message.chat.id, task)
#         else:
#             attempt += 1
#             if attempt > 3:
#                 bot.send_message(message.chat.id, 'Создание события отменено из-за превышения числа неудачных попыток')
#                 return None
#             msg = bot.send_message(message.chat.id,
#                                    f'Пользователь {message.text} не существует, либо он не инициализирован. \n'
#                                    f'Для инициализации пользователю {message.text} необходимо отправить в чат команду \n/init\n'
#                                    f'Укажите пользователя, для которого нужно назначить задание. Например @{message.from_user.username}')
#             bot.register_next_step_handler(msg, task_commit, task, attempt)
#     else:
#         task.db_export()
#         bot.send_message(message.chat.id, task)


#TODO Добавить функцию добавления таски, универсальную для себя или для другого пользователя - готово
#TODO Добавить функцию редактирования таски. Возможно, потребуется добавить поле "creator_id"
# которая будет использовваться для защиты от изменения таски другими пользователями

#TODO Протестировать создание таски от неинициализированного пользователя
#TODO Протестировать добавление таски для неинициализированного пользователя

tbot.polling(none_stop=True)
