from random import choice

from datetime import datetime, timedelta

import time

import asyncio

from aiogram import types, executor
from aiogram.utils.exceptions import BotBlocked
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command


from localization import start_or_help_command, about_bot_command, feedback_messages, feedback_report, cancel, \
    command_error, lang_button, language_changing, ban, length_limit, processing_phrase, prompt, response_lang

from databases import users_table_creation, dialogues_table_creation, errors_table_creation, counter_table_creation, \
    user_info, new_message, new_error, current_requests_num_change, \
    language_retrieving, last_nine_messages_retrieving, all_users, banned_users, processing_error_status_retrieving, \
    no_answer_requests

from message_processing import bot, dp, FeedbackForm, \
    keyboard, cancel_button, \
    typing_animation, error_notification, bot_was_stopped_sorry, \
    gpt_response_creation

from config import admin_chat_id, standard_lang, restriction, max_dialog_len, delta_time


# ----------------
# при запуске бота
# ----------------


# запуск программы (соответственно, бота)
def polling():
    try:
        executor.start_polling(dispatcher=dp, on_startup=on_startup)
    except Exception as error:
        new_error(str(error), datetime.utcnow(), None, None)
        time.sleep(10)
        polling()


# при запуске бота
async def on_startup(_):
    print(' ❗ Бот запущен!')

    users_table_creation()
    errors_table_creation()
    counter_table_creation()

    await bot_was_stopped_sorry()


# --------------------------------------
# для использования во время этой сессии
# --------------------------------------


# очередь на отправку запроса в OpenAI
queue = tuple()
# номер сообщения
num = 1


# ---------------------
# обработчики сообщений
# ---------------------


# отвечаем забаненым (их статус меняется вручную в БД)
@dp.message_handler(lambda message: message.chat.id in banned_users())
async def banned_user_message(message: types.Message):
    chat_id = message.chat.id
    lang = language_retrieving(chat_id)

    current_requests_num_change(chat_id, no_answer_requests(chat_id) + 1)
    error_code = 0
    try:
        bot_message = await message.answer(ban[lang] + str(chat_id) + '.')
        await asyncio.sleep(10)
        await message.delete()
        await bot_message.delete()
    except Exception as error:
        await error_notification(error, chat_id, error_code, message.from_user.username, lang)
    finally:
        current_requests_num_change(chat_id, no_answer_requests(chat_id) - 1)


@dp.message_handler(commands=['start', 'help'])
async def start_command(message: types.Message):
    chat_id = message.chat.id

    dialogues_table_creation(chat_id)
    lang, processing_error_status = (standard_lang, 0) if chat_id not in all_users() else \
        (language_retrieving(chat_id), processing_error_status_retrieving(chat_id))
    error_code = 1
    try:
        user_info(chat_id, message.from_user.username, lang, processing_error_status)
        current_requests_num_change(chat_id, no_answer_requests(chat_id) + 1)
        new_message(chat_id, 'command', 'user', message.text, datetime.utcnow())
        bot_message = await message.answer(start_or_help_command[lang], reply_markup=keyboard(chat_id))
        new_message(chat_id, 'command', 'assistant', bot_message.text, datetime.utcnow())
    except Exception as error:
        await error_notification(error, chat_id, error_code, message.from_user.username, lang)
    finally:
        current_requests_num_change(chat_id, no_answer_requests(chat_id) - 1)


@dp.message_handler(commands=['about'])
async def about_command(message: types.Message):
    chat_id = message.chat.id
    lang = language_retrieving(chat_id)

    new_message(chat_id, 'command', 'user', message.text, datetime.utcnow())
    current_requests_num_change(chat_id, no_answer_requests(chat_id) + 1)
    error_code = 2
    try:
        bot_message = await message.answer(about_bot_command[lang] + str(chat_id) + '.')

        new_message(chat_id, 'command', 'assistant', bot_message.text, datetime.utcnow())
    except Exception as error:
        await error_notification(error, chat_id, error_code, message.from_user.username, lang)
    finally:
        current_requests_num_change(chat_id, no_answer_requests(chat_id) - 1)


@dp.message_handler(Command('feedback'))
async def feedback_command(message: types.Message):
    chat_id = message.chat.id
    lang = language_retrieving(chat_id)

    new_message(chat_id, 'command', 'user', message.text, datetime.utcnow())
    current_requests_num_change(chat_id, no_answer_requests(chat_id) + 1)
    error_code = 3
    try:
        bot_message = await message.answer(choice(feedback_messages[lang]), reply_markup=cancel_button())

        new_message(chat_id, 'command', 'assistant', bot_message.text, datetime.utcnow())

        await FeedbackForm.Waiting_for_feedback.set()
    except Exception as error:
        await error_notification(error, chat_id, error_code, message.from_user.username, lang)


# получаем отзыв пользователя следующим сообщением
@dp.message_handler(state=FeedbackForm.Waiting_for_feedback)
async def feedback_process(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    lang = language_retrieving(chat_id)

    new_message(chat_id, 'command', 'user', message.text, datetime.utcnow())
    error_code = 4
    try:
        if message.text in ('/start', '/help', '/about'):
            await message.answer(choice(command_error[lang]))
            return
        else:
            await state.finish()
            if message.text.strip() == '/cancel':
                bot_message = await message.answer(cancel[lang], reply_markup=keyboard(chat_id))
            else:
                bot_message = await message.answer(choice(feedback_report[lang]), reply_markup=keyboard(chat_id))
                report = await bot.send_message(admin_chat_id, '❗ ПОДЪЕХАЛ ФИДБЕК !')
                feedback = await bot.forward_message(admin_chat_id, chat_id, message.message_id)
                await bot.pin_chat_message(admin_chat_id, feedback.message_id, disable_notification=False)
                new_message(admin_chat_id, 'command', 'assistant', report.text, datetime.utcnow())
                new_message(admin_chat_id, 'command', 'assistant', feedback.text, datetime.utcnow())
        new_message(chat_id, 'command', 'assistant', bot_message.text, datetime.utcnow())
    except Exception as error:
        await error_notification(error, chat_id, error_code, message.from_user.username, lang)
    finally:
        current_requests_num_change(chat_id, no_answer_requests(chat_id) - 1)


@dp.message_handler(commands=['РАССЫЛКА:'])
async def mailing_command(message: types.Message):
    chat_id = message.chat.id
    lang = language_retrieving(chat_id)

    new_message(chat_id, 'command', 'user', message.text, time)
    current_requests_num_change(chat_id, no_answer_requests(chat_id) + 1)
    error_code = 5
    try:
        if message.chat.id == admin_chat_id:
            users = all_users()
            total_users = len(users)
            admin_message = message.text[11:]
            for user in users:
                try:
                    await bot.send_message(user, admin_message)
                    new_message(user, 'command', 'assistant', admin_message, datetime.utcnow())
                except BotBlocked:
                    total_users -= 1
            bot_message = await message.reply(f'Ваше сообщение было доставлено всем доступным пользователям '
                                              f'({total_users}/{len(users)})!')
        else:
            bot_message = await message.answer(choice(command_error[lang]))
        new_message(chat_id, 'command', 'assistant', bot_message.text, time)
    except Exception as error:
        await error_notification(error, chat_id, error_code, message.from_user.username, lang)
    finally:
        current_requests_num_change(chat_id, no_answer_requests(chat_id) - 1)


@dp.message_handler(content_types=['text'])
async def message_handle(message: types.Message):
    global queue, num, last_use_time

    chat_id = message.chat.id
    lang = language_retrieving(chat_id)

    # получаем историю
    dialog = last_nine_messages_retrieving(chat_id)
    messages = tuple(phrase[1] for phrase in dialog)
    final_message = message.text[:restriction[lang][0]]
    new_message(chat_id, 'message', 'user', final_message, datetime.utcnow())

    current_requests_num_change(chat_id, no_answer_requests(chat_id) + 1)
    error_code = 7
    try:
        # какая-то неизвестная команда
        if message.text[0] == '/':
            bot_message = await message.answer(choice(command_error[lang]))
        # не команда
        else:
            error_code = 8
            # смена языка
            if message.text.capitalize().strip() in lang_button:
                lang = abs(lang - 1)
                user_info(chat_id, message.from_user.username, lang, processing_error_status_retrieving(chat_id))
                bot_message = await message.answer(choice(language_changing[lang]), reply_markup=keyboard(chat_id))

            # вопрос/сообщения для GPT
            else:
                error_code = 9

                # встали в очередь
                pos, num = num, num + 1
                queue += (pos, )

                # если общее число символов превышает максимальное, мы удаляем часть истории
                total = 0
                for first_message in range(-1, -1 - len(messages), -1):
                    if len(''.join(messages)[first_message:]) < max_dialog_len[lang]:
                        total = first_message
                    else:
                        break

                # итоговая история сообщений для передачи нейронке
                context = [{'role': 'system', 'content': prompt + response_lang[lang]}] + \
                    [{'role': phrase_data[0], 'content': phrase_data[1]} for phrase_data in dialog[total:]] + \
                    [{'role': 'user', 'content': final_message}]

                # анимация набора сообщения
                task = asyncio.create_task(typing_animation(chat_id))

                try:
                    error_code = 10
                    # отправляем уведомление об ограничении длины сообщения
                    if len(message.text) > restriction[lang][0]:
                        await bot.send_message(message.chat.id, length_limit[lang])
                    loading = await message.reply(choice(processing_phrase[lang]))

                    # ожидание очереди
                    while queue.index(pos) != 0 or last_use_time + timedelta(seconds=delta_time) > datetime.utcnow():
                        await asyncio.sleep(1)

                    # ответ нейронки
                    gpt_answer = gpt_response_creation(context, lang)

                    # отправляем ответ
                    await loading.delete()
                    bot_message = await message.reply(gpt_answer)
                finally:
                    # двигаем очередь
                    queue, last_use_time = queue[1:], datetime.utcnow()
                    await asyncio.sleep(0.2)
                    task.cancel()
        new_message(chat_id, 'message', 'assistant', bot_message.text, datetime.utcnow())
    except Exception as error:
        await error_notification(error, chat_id, error_code, message.from_user.username, lang)
    finally:
        current_requests_num_change(chat_id, no_answer_requests(chat_id) - 1)


if __name__ == '__main__':
    last_use_time = datetime.utcnow()
    polling()
