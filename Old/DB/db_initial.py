import os.path
import sqlite3

db_directory = os.path.join(os.path.dirname(__file__), 'db.sqlite3')


if __name__ == '__main__':
    connection = sqlite3.connect(db_directory)
    cursor = connection.cursor()

    connection.execute('PRAGMA foreign_keys = 1')

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS USERS (
    id INTEGER PRIMARY KEY,
    is_superuser INTEGER NOT NULL,
    firstname TEXT NOT NULL,
    username TEXT NOT NULL,
    chat_id INTEGER NOT NULL
    )
    
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TASKS (
    id INTEGER PRIMARY KEY,
    header TEXT NOT NULL,
    description TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    complete INTEGER NOT NULL,
    user_id INTEGER,
    creator_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES USERS (id)
    FOREIGN KEY (creator_id) REFERENCES USERS (id)
    )
    """)

    connection.commit()
    connection.close()


