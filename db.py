# -*- coding: utf-8 -*-
import config
import sqlite3
from config import db_name


class Db:

    def __init__(self):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()

    def close(self):
        self.connection.close()

    def create_event(self, chat_id, message_id, owner_id, username, type_id):
        with self.connection:
            self.cursor.execute(
                'INSERT INTO events(message_id, chat_id, owner_id, username, type_id) VALUES (?, ?, ?, ?, ?)', (message_id, chat_id, owner_id, username, type_id))
            return self.cursor.lastrowid

    def create_answer(self, chat_id, message_id, user_id, username, answer):
        with self.connection:
            self.cursor.execute(
                'INSERT INTO answers(user_id, answer, username, event_id) VALUES (?,?,?, (SELECT id FROM events WHERE chat_id= ? AND message_id = ?))', (user_id, answer, username, chat_id, message_id))
            return self.cursor.lastrowid

    def select_event(self, chat_id, message_id):
        with self.connection:
            return self.cursor.execute("SELECT username, type_id FROM events WHERE chat_id = ? AND message_id = ?", (chat_id, message_id)).fetchall()

    def select_answer(self, chat_id, message_id, user_id):
        with self.connection:
            return self.cursor.execute("SELECT 1 FROM answers WHERE user_id = ? AND event_id = (SELECT id FROM events WHERE message_id = ? AND chat_id = ?)", (user_id, message_id, chat_id)).fetchall()

    def select_answers_filter(self, chat_id, message_id, answer):
        with self.connection:
            return self.cursor.execute("SELECT username FROM answers WHERE answer = ? AND event_id = (SELECT id FROM events WHERE message_id = ? AND chat_id = ?)", (answer, message_id, chat_id)).fetchall()
    
    def select_answers(self, chat_id, message_id):
        with self.connection:
            return self.cursor.execute(" \
            SELECT answer, group_concat(username, ', ') \
            FROM answers \
            WHERE event_id = (SELECT id FROM events WHERE message_id = ? AND chat_id = ?) \
            GROUP BY answer", (message_id, chat_id)).fetchall()

    def get_owner(self, chat_id, message_id):
        with self.connection:
            result = self.cursor.execute(
                'SELECT owner_id FROM events WHERE message_id = ? AND chat_id = ?', (message_id, chat_id)).fetchone()
            if result:
                return result[0]
            else:
                return None
    
    def delete_event(self, chat_id, message_id):
        with self.connection:
            self.cursor.execute('DELETE FROM answers WHERE event_id = (SELECT id FROM events WHERE chat_id = ? AND message_id = ?)', (chat_id, message_id))
            self.cursor.execute('DELETE FROM events WHERE chat_id = ? AND message_id = ?', (chat_id, message_id))
