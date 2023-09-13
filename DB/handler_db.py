import sqlite3

if __name__ == '__main__':
    from db_initial import db_directory
else:
    from .db_initial import db_directory


""" 
    Блок содержит методы обращений к базе данных. любое обращение оборачивается в декоратор @db_request_wrapper
"""


def db_request_wrapper(request):
    def wrapper(*args, **kwargs):
        connection = sqlite3.connect(db_directory, check_same_thread=False)
        cursor = connection.cursor()
        cursor.execute(request(*args, **kwargs)[0], request(*args, **kwargs)[1])
        result = cursor.fetchall()
        connection.commit()
        connection.close()
        return result
    return wrapper


@db_request_wrapper
def new_user(firstname, username, chat_id):
    return 'INSERT INTO USERS (is_superuser, firstname, username, chat_id) VALUES (?, ?, ?, ?)', (0, firstname, username, chat_id)


@db_request_wrapper
def new_task(header, description, date, time, complete, user_id, creator_id):
    return \
        'INSERT INTO TASKS (header, description, date, time, complete, user_id, creator_id) VALUES (?, ?, ?, ?, ?, ?, ?)', \
            (header, description, date, time, complete, user_id, creator_id)


@db_request_wrapper
def get_user_id(username, chat_id):
    return 'SELECT id FROM USERS WHERE username = ? AND chat_id = ?', (username, chat_id)


@db_request_wrapper
def update_user(user_id, field, value):
    return f'UPDATE USERS SET {field} = ? WHERE id = ?', (value, user_id)


# new_user('Антончик213', 'sa1nttony2', 123)
# new_user('Антончикc', 'sa1ntt', 231)
# new_task('Вкусно покушать', 'С утра с кофе еще и вкусно покушать', '2023-08-29', '10:35:00', 0, 2)
# print(get_user_id('Антончикc', 231)[0][0])

# w = get_user_id('sa1nttony2', 1234)
# if w:
#     print(w)
# else:
#     print('nothing')