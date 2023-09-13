from handler_db import db_request_wrapper


class User:
    def __init__(self, firstname, username):
        self.firstname = firstname
        self.username = username

    @db_request_wrapper
    def new_user(self, firstname, username):
        return 'INSERT INTO USERS (firstname, username) VALUES (?, ?)', (firstname, username)
