import datetime

import requests
import telegram_bot_calendar
import datetime
import json



# resp = requests.get("http://localhost:8000/api/tasks/id=1")
# data = resp.json()
# print(data[0]['id'])

# BASE = "http://localhost:8000/api"
#
# def request_account_create(firstname, username, telegram_id):
#     utl = f"{BASE}/users/"
#     body = {
#         'firstname': firstname,
#         'username': username,
#         'telegram_id': telegram_id,
#         'password': '123456'
#     }
#     request = requests.post(utl, body)
#     return request.json()
#
# print(request_account_create('test11', 'tes11t1', 1234556))

# p = requests.get(f"{BASE}/users/telegram_id=1")
# if p:
#     print(123)

print(datetime.datetime.now().minute)


user = {
            'telegram_id': 123
        }
task = {
            'id': 123,
            'header': 23,
            'description': 3,
            "date": datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%dT%H:%M:%SZ')
        }
print(json.dumps([user, task]))