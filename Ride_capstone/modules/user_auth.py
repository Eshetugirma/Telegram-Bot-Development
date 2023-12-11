# modules/user_auth.py
from aiogram import types, Dispatcher, F
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.markdown import hbold
from aiogram.fsm.state import State, StatesGroup
from my_callback import MyCallback

class Form(StatesGroup):
    id = State()
    fullname = State()
    phone = State()
    role = State()
    date = State()
    history = State()
    current_location = State()
    destination = State()

callback_registration = MyCallback()

async def user_start(message: types.Message):
    # Handle user start
    pass

async def user_registration(query: types.CallbackQuery, callback_data: MyCallback, state: FSMContext):
    # Handle user registration
    pass
