import telebot

from flask import Flask, request

from config import TOKEN
from utils import convert_datetime_for_obj, convert_to_user_tz
tbot = telebot.TeleBot(TOKEN, threaded=True, num_threads=300, parse_mode='HTML')

def send_remind(task, user):
    text = f"""<strong>‼️ Наступило время события ‼️:</strong>
<strong>Название</strong>: <em>{task['header']}</em>
<strong>Описание</strong>: <em>{task['description']}</em>
<strong>Дата и время</strong>: <em>{convert_to_user_tz(convert_datetime_for_obj(task['date']), user['telegram_id']).strftime("%d.%m.%Y %H:%M")}</em>"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text="✅ Завершить", callback_data=f"finish_task:{task['id']}"))
    markup.row(
        telebot.types.InlineKeyboardButton(text="Перенести: 5 мин.", callback_data=f"move_task:{task['id']}:5m"),
        telebot.types.InlineKeyboardButton(text="Перенести: 10 мин.", callback_data=f"move_task:{task['id']}:10m")
    )
    markup.row(
        telebot.types.InlineKeyboardButton(text="Перенести: 15 мин.", callback_data=f"move_task:{task['id']}:15m"),
        telebot.types.InlineKeyboardButton(text="Перенести: 30 мин.", callback_data=f"move_task:{task['id']}:30m")
    )
    markup.row(
        telebot.types.InlineKeyboardButton(text="Перенести: 1 час", callback_data=f"move_task:{task['id']}:1h"),
        telebot.types.InlineKeyboardButton(text="Перенести: 3 часа", callback_data=f"move_task:{task['id']}:3h")
    )
    markup.row(
        telebot.types.InlineKeyboardButton(text="Перенести: 6 часов", callback_data=f"move_task:{task['id']}:6h"),
        telebot.types.InlineKeyboardButton(text="Перенести: Сутки", callback_data=f"move_task:{task['id']}:1d")
    )
    tbot.send_message(user['telegram_id'], text, reply_markup=markup)


app = Flask('app')

@app.route('/send_remind', methods=['POST'])
def send_reminder():
    data = request.json
    user = data['user']
    task = data['task']
    send_remind(task, user)
    return {'success': True}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)