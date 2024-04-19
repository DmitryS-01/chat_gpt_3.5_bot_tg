from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import bot_api_key


# бот
bot = Bot(bot_api_key)
dp = Dispatcher(bot, storage=MemoryStorage())


# для получения отзыва через /feedback
class FeedbackForm(StatesGroup):
    Waiting_for_feedback = State()
