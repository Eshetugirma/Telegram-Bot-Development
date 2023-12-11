# modules/profile_management.py
from aiogram import types, FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from my_callback import MyCallback

async def edit_fullname(query: types.CallbackQuery, state: FSMContext):
    # Handle profile editing
    pass

async def process_edit_name(message: types.Message, state: FSMContext):
    # Handle updating user's full name in the database
    pass
