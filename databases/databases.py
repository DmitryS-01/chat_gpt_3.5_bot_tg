import sqlite3
import os


# -------------------
# создаем базы данных
# -------------------


# все файлы БД

# папка
databases_dir = os.path.dirname(__file__)

# файлы БД
settings_db = os.path.join(databases_dir, 'settings.db')
dialogues_db = os.path.join(databases_dir, 'dialogues.db')
errors_db = os.path.join(databases_dir, 'errors.db')


# все пользователи и их настройки
def users_table_creation():
    with sqlite3.connect(settings_db) as db:
        cursor = db.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS users(
                       chat_id INT, 
                       username TEXT,
                       lang INT, 
                       is_not_banned INT, 
                       processing_error INT,
                       current_requests INT, 
                       note TEXT
                       )""")
        db.commit()


# диалоги
def dialogues_table_creation(chat_id):
    user_chat_id = f'user_{chat_id}'
    with sqlite3.connect(dialogues_db) as db:
        cursor = db.cursor()
        cursor.execute(f"""CREATE TABLE IF NOT EXISTS {user_chat_id}(
                       message_id TEXT,
                       message_type TEXT,
                       role TEXT,
                       message TEXT,
                       time TEXT
                       )""")
        db.commit()


# ошибки
def errors_table_creation():
    with sqlite3.connect(errors_db) as db:
        cursor = db.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS logs(
                       error TEXT, 
                       time TEXT,
                       chat_id INT, 
                       error_code INT
                       )""")
        db.commit()


# номер сообщения
def counter_table_creation():
    with sqlite3.connect(dialogues_db) as db:
        cursor = db.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS counter(
                       num TEXT,
                       chat_id INT
                       )""")
        cursor.execute("""SELECT num 
                       FROM counter""")
        message_id = cursor.fetchone()
        if message_id is None:
            cursor.execute("""INSERT INTO counter
                           (num) 
                           VALUES(?)""",
                           [1])
        db.commit()


# --------------------------------------
# дописываем и/или обновляем данные в БД
# --------------------------------------


# пользователь ввел /start, добавляем его в общую базу
def user_info(chat_id, username, lang, processing_error_status):
    username_tg = f'@{username}' if username is not None else None
    with sqlite3.connect(settings_db) as db:
        cursor = db.cursor()
        cursor.execute("""SELECT chat_id 
                       FROM users 
                       WHERE chat_id = ?""",
                       [chat_id])
        already_exists = cursor.fetchone()
        if already_exists is None:
            # русский язык = 0, английский = 1
            cursor.execute("""INSERT INTO users
                           (chat_id, username, lang, is_not_banned, processing_error, current_requests) 
                           VALUES(?, ?, ?, ?, ?, ?)""",
                           [chat_id, username_tg, lang, 1, 0, 0])
        else:
            cursor.execute("""UPDATE users 
                           SET (username, lang, processing_error)  = (?, ?, ?) 
                           WHERE chat_id = ?""",
                           [username_tg, lang, processing_error_status, chat_id])
        db.commit()


# пользователь написал сообщение, запоминаем его (сохраняем историю диалога)
def new_message(chat_id, message_type, role, message, time):
    user_chat_id = f'user_{chat_id}'
    with sqlite3.connect(dialogues_db) as db:
        cursor = db.cursor()
        cursor.execute("""SELECT num 
                       FROM counter""")
        message_id = cursor.fetchone()[0]
        cursor.execute("""UPDATE counter
                       SET (num, chat_id) = (?, ?)""",
                       [int(message_id) + 1, chat_id])
        cursor.execute(f"""INSERT INTO {user_chat_id}
                       (message_id, message_type, role, message,time) 
                       VALUES(?, ?, ?, ?, ?)""",
                       [message_id, message_type, role, str(message), time])
        db.commit()


# меняем число сообщений, на которые не был дан ответ
def current_requests_num_change(chat_id, new_requests_num):
    with sqlite3.connect(settings_db) as db:
        cursor = db.cursor()
        cursor.execute("""UPDATE users 
                       SET current_requests  = ?
                       WHERE chat_id = ?""",
                       [new_requests_num, chat_id])
        db.commit()


# записываем ошибку в логи
def new_error(error, time, chat_id, error_code):
    with sqlite3.connect(errors_db) as db:
        cursor = db.cursor()
        cursor.execute(f"""INSERT INTO logs
                       (error, time, chat_id, error_code) 
                       VALUES(?, ?, ?, ?)""",
                       [error, time, chat_id, error_code])
        db.commit()


# ----------------------------
# достаем из баз нужные данные
# ----------------------------


# язык
def language_retrieving(chat_id):
    with sqlite3.connect(settings_db) as db:
        cursor = db.cursor()
        cursor.execute("""SELECT lang 
                       FROM users 
                       WHERE chat_id = ?""",
                       [chat_id])
        lang = cursor.fetchone()
    return lang[0]


# последние 10 сообщений
def last_nine_messages_retrieving(chat_id):
    user_chat_id = f'user_{chat_id}'
    with sqlite3.connect(dialogues_db) as db:
        cursor = db.cursor()
        cursor.execute(f"""SELECT role, message
                       FROM {user_chat_id} 
                       WHERE message_type = 'message'""")
        messages = cursor.fetchall()[-9:]
    return tuple(messages)


# ВСЕ пользователи бота
def all_users():
    with sqlite3.connect(settings_db) as db:
        cursor = db.cursor()
        cursor.execute(f"""SELECT chat_id 
                       FROM users""")
        users = cursor.fetchall()
    users_tuple = tuple(user[0] for user in users)
    return users_tuple


# забанены
def banned_users():
    with sqlite3.connect(settings_db) as db:
        cursor = db.cursor()
        cursor.execute(f"""SELECT chat_id
                       FROM users
                       WHERE is_not_banned = 0""")
        users = cursor.fetchall()
    users_tuple = tuple(user[0] for user in users)
    return users_tuple


# была ли ошибка
def processing_error_status_retrieving(chat_id):
    with sqlite3.connect(settings_db) as db:
        cursor = db.cursor()
        cursor.execute("""SELECT processing_error
                       FROM users
                       WHERE chat_id = ?""",
                       [chat_id])
        status = cursor.fetchone()
    return status[0]


# ВСЕ пользователи, которые не получили ответ
def no_answer_users():
    with sqlite3.connect(settings_db) as db:
        cursor = db.cursor()
        cursor.execute("""SELECT chat_id
                       FROM users
                       WHERE current_requests > 0""")
        users = cursor.fetchall()
    users_tuple = tuple(user[0] for user in users)
    return users_tuple


# число запросов, на которые не был дан ответ
def no_answer_requests(chat_id):
    with sqlite3.connect(settings_db) as db:
        cursor = db.cursor()
        cursor.execute("""SELECT current_requests
                       FROM users
                       WHERE chat_id = ?""",
                       [chat_id])
        status = cursor.fetchone()
    return status[0]
