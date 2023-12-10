import telebot
import datetime
import random

from config import TOKEN
from phrases import commands, example_headers, example_descriptions, hints
from ReminderBot.bot.models import Account, Chat, ChatUser, Task
# from DB.handler_db import new_user, new_task, get_user_id, update_user
from utils import UserAlreadyExist, Task, add_new_user, user_exist


bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start', 'help'])
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
    bot.reply_to(message, text)


@bot.message_handler(commands=['init'])
def init_user(message: telebot.types.Message):
    firstname = message.from_user.first_name
    username = message.from_user.username
    chat_id = message.chat.id
    try:
        add_new_user(firstname, username, chat_id)
    except UserAlreadyExist as e:
        bot.reply_to(message, f'Ошибка: {e}')
    else:
        bot.reply_to(message, f'Пользователь {firstname} успешно инициализирован')


@bot.message_handler(commands=['admin'])
def create_superuser(message: telebot.types.Message):
    username = message.from_user.username
    chat_id = message.chat.id
    user_id = get_user_id(username, chat_id)[0][0]
    update_user(user_id, 'is_superuser', 1)
    text = f'{message.from_user.first_name} теперь может давать задания другим пользователям чата'
    bot.reply_to(message, text)


#Блок создания задания
@bot.message_handler(commands=['new_task'])
def start_new_task(message: telebot.types.Message):
    start_message = message
    task = Task()
    msg = bot.send_message(message.chat.id,
                           f'Укажите короткое описание события. Например "{example_headers[random.randint(0, len(example_headers)-1)]}"')
    bot.register_next_step_handler(msg, task_header, task, start_message)


def task_header(message, task, start_message):
    task.get_header = message.text
    msg = bot.send_message(message.chat.id,
                           f'Укажите более подробное описание события. Например "{example_descriptions[random.randint(0, len(example_headers)-1)]}"')
    bot.register_next_step_handler(msg, task_date, task, start_message)


def task_date(message, task, start_message):
    task.get_description = message.text
    msg = bot.send_message(message.chat.id, f'Укажите дату события в формате "ДД ММ ГГГГ". Например "{datetime.date.today().strftime("%d %m %Y")}"')
    bot.register_next_step_handler(msg, task_time, task, start_message)


def task_time(message, task, start_message):
    try:
        task.get_date = message.text
    except Exception as e:
        msg = bot.send_message(message.chat.id,
                               f'{e}\nУкажите дату события в формате "ДД ММ ГГГГ". Например "{datetime.date.today().strftime("%d %m %Y")}"')
        bot.register_next_step_handler(msg, task_time, task, start_message)
    else:
        msg = bot.send_message(message.chat.id,
                               f'Укажите время события в формате "ЧЧ:ММ". Например "{datetime.datetime.now().strftime("%H:%M")}"')
        bot.register_next_step_handler(msg, task_user, task, start_message)


def task_user(message, task, start_message):
    try:
        task.get_time = message.text
    except Exception as e:
        msg = bot.send_message(message.chat.id,
                               f'{e}\nУкажите время события в формате "ЧЧ:ММ". Например "{datetime.datetime.now().strftime("%H:%M")}"')
        bot.register_next_step_handler(msg, task_user, task, start_message)
    else:
        if user_exist(start_message.from_user.username, message.chat.id):
            task.get_creator_id = get_user_id(start_message.from_user.username, message.chat.id)[0][0]
            if start_message.from_user.id == message.chat.id:
                task.get_user_id = task.get_creator_id
                task_commit(start_message, task)
            else:
                msg = bot.send_message(message.chat.id,
                                       f'Укажите пользователя, для которого нужно назначить задание. Например @{start_message.from_user.username}')
                bot.register_next_step_handler(msg, task_commit, task)
        else:
            bot.send_message(message.chat.id, f'Пользователь {start_message.from_user.username} не был инициализирован. \n'
                                              f'Для инициализации, пользователь должен отправить команду /init')


def task_commit(message, task, attempt=0):
    if not task.get_user_id:
        if user_exist(message.text.replace('@', ''), message.chat.id):
            task.get_user_id = get_user_id(message.text.replace('@', ''), message.chat.id)[0][0]
            try:
                task.db_export()
            except Exception as e:
                msg = f'{e}\n'
                for hint in hints:
                    msg = msg + hint
                bot.send_message(message.chat.id, msg)
            else:
                bot.send_message(message.chat.id, task)
        else:
            attempt += 1
            if attempt > 3:
                bot.send_message(message.chat.id, 'Создание события отменено из-за превышения числа неудачных попыток')
                return None
            msg = bot.send_message(message.chat.id,
                                   f'Пользователь {message.text} не существует, либо он не инициализирован. \n'
                                   f'Для инициализации пользователю {message.text} необходимо отправить в чат команду \n/init\n'
                                   f'Укажите пользователя, для которого нужно назначить задание. Например @{message.from_user.username}')
            bot.register_next_step_handler(msg, task_commit, task, attempt)
    else:
        task.db_export()
        bot.send_message(message.chat.id, task)


#TODO Добавить функцию добавления таски, универсальную для себя или для другого пользователя - готово
#TODO Добавить функцию редактирования таски. Возможно, потребуется добавить поле "creator_id"
# которая будет использовваться для защиты от изменения таски другими пользователями

#TODO Протестировать создание таски от неинициализированного пользователя
#TODO Протестировать добавление таски для неинициализированного пользователя

bot.polling(none_stop=True)
