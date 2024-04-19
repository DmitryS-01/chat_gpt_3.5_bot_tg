from random import choice

from datetime import datetime

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

import asyncio

from databases import user_info, processing_error_status_retrieving

from localization import lang_button, bot_error

from databases import current_requests_num_change, new_error, \
    language_retrieving, no_answer_users

from .bot import bot


# ----------
# клавиатуры
# ----------


# клавиатура стандарт
def keyboard(chat_id):
    lang = language_retrieving(chat_id)
    button = KeyboardButton(lang_button[lang])
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(button)
    return markup


# клава в /feedback
def cancel_button():
    button = KeyboardButton('/cancel')
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(button)
    return markup


# ------------------------
# обработка ошибок и т. п.
# ------------------------


# анимация набора сообщения в чате с ботом
async def typing_animation(chat_id):
    while True:
        await bot.send_chat_action(chat_id, 'typing')
        await asyncio.sleep(1.5)


# отправляем сообщение об ошибке в чат с пользователем
async def error_report(chat, error_code, lang):
    while True:
        try:
            await bot.send_message(chat, choice(bot_error[lang]))
            break
        except Exception as error:
            # прописал старт и кинул в бан((( можно игнорировать обновления при запуске бота, чтобы этого не было
            if str(error) == 'Forbidden: bot was blocked by the user':
                break
            new_error(str(error), datetime.utcnow(), chat, error_code)
            print(f'Ошибка:\n{str(error)}')
            await asyncio.sleep(5)


# даже если ошибок несколько, отправится только 1 уведомление
async def error_notification(error, chat_id, error_code, username, lang):
    new_error(str(error), datetime.utcnow(), chat_id, error_code)
    print(f'Ошибка! Код ошибки (в хендлерах) - {str(error_code)}:\n{str(error)}')
    if processing_error_status_retrieving(chat_id) == 0:
        user_info(chat_id, username, lang, 1)
        await error_report(chat_id, error_code, lang)
        user_info(chat_id, username, lang, 0)


# отправляем сообщение об ошибке пользователям, обработка запросов которых была прервана из-за остановки программы
async def bot_was_stopped_sorry():
    for user in no_answer_users():
        lang = language_retrieving(user)
        try:
            await bot.send_message(user, choice(bot_error[lang]))
            current_requests_num_change(user, 0)
        except Exception as error:
            new_error(str(error), datetime.utcnow(), user, None)
            print(f'Ошибка!\n{str(error)}')
            continue
