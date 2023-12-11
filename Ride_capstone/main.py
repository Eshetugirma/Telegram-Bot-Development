
import json
import sqlite3
import asyncio
import random
import re
import logging
import sys
from os import getenv
from datetime import datetime
from aiogram.methods.get_user_profile_photos import GetUserProfilePhotos
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F, Router, html
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

from finite_state_machine_bot import Form
from my_callback import MyCallback
from passenger_role_handler import process_passenger_role
from send_ride_alert import send_new_passenger_notification
from user_profile_handler import process_user_profile
from driver_role_handler import process_driver_role

# Load environment variables from the .env file
load_dotenv()
form_router = Router()

TOKEN = getenv("RIDE_TOKEN")
if TOKEN is None:
    raise ValueError("Telegram token is not set.")

dp = Dispatcher()
form_router = Router()

# START: COMMAND
@form_router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    user_id = message.chat.id
    conn = sqlite3.connect('ride_healing/users.db')
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT fullname, phone, completed_rides FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

        if result:
            await handle_existing_user(result, message)
        else:
            await handle_new_user(state, message)
    except Exception as e:
        print(f"Error fetching data from the database: {e}")
    finally:
        conn.close()

async def handle_existing_user(result, message):
    menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🚘 Book Ride', callback_data=MyCallback(name="ride", id="4").pack()),
         InlineKeyboardButton(text='🔁 Driver Matching', callback_data=MyCallback(name="match", id="5").pack())],
        [InlineKeyboardButton(text='⭐️ Rate Driver', callback_data=MyCallback(name="rate", id="6").pack()),
         InlineKeyboardButton(text='🧾 History', callback_data=MyCallback(name="history", id="7").pack())],
        [InlineKeyboardButton(text='⚙️ Profile', callback_data=MyCallback(name="profile", id="8").pack())], ], )
    await message.answer(f"{hbold('Welcome to Ride Healing Bot 🚖')}!\n\nSteer your ride! Where would you like to go?😎\nSelect from features ..  ", reply_markup=menu)

async def handle_new_user(state, message):
    await state.set_state(Form.fullname)
    menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='▶️ Registration', callback_data=MyCallback(name="registration", id="0").pack())]
    ])
    await message.answer(f"Hi, {hbold('Welcome to Ride Healing Bot 🚖')}!\nPlease register to continue.", reply_markup=menu)

# REGISTRATION: CALLBACK QUERY
@form_router.callback_query(MyCallback.filter(F.name == "registration"))
async def my_callback_foo(query: types.CallbackQuery, callback_data: MyCallback):
    await query.message.delete()
    await query.message.answer(f"Please enter your full name to continue.")
    print("Clicked =", callback_data.id)

# FULL NAME: PROCESS
@form_router.message(Form.fullname)
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(fullname=message.text)
    await state.update_data(date=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    await state.update_data(id=message.chat.id)

    await state.set_state(Form.phone)
    await message.answer(
        "Please share your phone number by clicking the button below.",
        reply_markup=ReplyKeyboardMarkup(keyboard=[
            [
                KeyboardButton(text="Share Phone Number", request_contact=True),
            ]
        ], resize_keyboard=True),
    )

# PHONE NUMBER: PROCESS   
@form_router.message(Form.phone)
async def process_phone_number(message: Message, state: FSMContext) -> None:
    phone_number = message.contact.phone_number
    await state.update_data(phone=phone_number)
    await state.set_state(Form.role)
    await message.answer(f"Processing phone number...",  reply_markup=ReplyKeyboardRemove())
    await message.delete()
    role = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🚖 Driver', callback_data=MyCallback(name="driver", id="1").pack()),
         InlineKeyboardButton(text='👤 Passenger', callback_data=MyCallback(name="passenger", id="2").pack())],
    ])
    await message.answer(f"Are you a driver or passenger.\nPlease, Choose role", reply_markup=role)

# DRIVER: CALLBACK QUERY
@form_router.callback_query(MyCallback.filter(F.name == "driver"))
async def callback_process_driver_role(query: types.CallbackQuery, callback_data: MyCallback, state: FSMContext):
    await process_driver_role(query, callback_data, state)

# PASSENGER: CALLBACK QUERY
@form_router.callback_query(MyCallback.filter(F.name == "passenger"))
async def callback_process_passenger(query: types.CallbackQuery, callback_data: MyCallback, state: FSMContext):
    await process_passenger_role(query, callback_data, state)

# DRIVER MATCHING: CALLBACK QUERY
@form_router.callback_query(MyCallback.filter(F.name == "match"))
async def process_match(query: types.CallbackQuery, callback_data: MyCallback):
    menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔙 Back', callback_data=MyCallback(name="home", id="3").pack())]])
    await query.message.answer(f"✅ Notification is on.\nYou will be notified when booking a ride", reply_markup=menu)

# RATE DRIVER: CALLBACK QUERY
@form_router.callback_query(MyCallback.filter(F.name == "rate"))
async def process_rate(query: types.CallbackQuery, callback_data: MyCallback):
    user_id = query.message.chat.id
    conn = sqlite3.connect('ride_healing/users.db')
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

        if result:
            user_role = result[0]

            if user_role == "driver":
                await rate_users(query, cursor, "passenger", "Rate {passenger[1]}", "No passengers available for rating.")

            elif user_role == "passenger":
                await rate_users(query, cursor, "driver", "Rate - {driver[1]}", "No drivers available for rating.")

            else:
                await query.message.answer("User role not recognized.")

        else:
            await query.message.answer("User not found in the database.")

    except Exception as e:
        print(f"Error fetching data from the database: {e}")
    finally:
        conn.close()

# HISTORY: CALLBACK QUERY
@form_router.callback_query(MyCallback.filter(F.name == "history"))
async def process_history(query: types.CallbackQuery, callback_data: MyCallback):
    user_id = query.message.chat.id
    conn = sqlite3.connect('ride_healing/users.db')
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

        if result:
            user_role = result[0]

            if user_role == "driver":
                await history_users(query, cursor, "passenger", "Ride history for {passenger[1]}", "No passengers available for history.")

            elif user_role == "passenger":
                await history_users(query, cursor, "driver", "Ride history for {driver[1]}", "No drivers available for history.")

            else:
                await query.message.answer("User role not recognized.")

        else:
            await query.message.answer("User not found in the database.")

    except Exception as e:
        print(f"Error fetching data from the database: {e}")
    finally:
        conn.close()

# PROFILE: CALLBACK QUERY
@form_router.callback_query(MyCallback.filter(F.name == "profile"))
async def process_profile(query: types.CallbackQuery, callback_data: MyCallback, state: FSMContext):
    await process_user_profile(query, callback_data, state)

# EDIT PROFILE: CALLBACK QUERY
@form_router.callback_query(MyCallback.filter(F.name == "edit_profile"))
async def process_edit_profile(query: types.CallbackQuery, callback_data: MyCallback, state: FSMContext):
    await process_user_profile(query, callback_data, state, edit_mode=True)

# EDIT FULL NAME: PROCESS
@form_router.message(Form.edit_fullname)
async def process_edit_fullname(message: Message, state: FSMContext):
    await state.update_data(fullname=message.text)
    await state.set_state(Form.edit_phone)
    await message.answer("Great! Now, please share your phone number by clicking the button below.",
                         reply_markup=ReplyKeyboardMarkup(keyboard=[
                             [KeyboardButton(text="Share Phone Number", request_contact=True)],
                         ], resize_keyboard=True))

# Handle the user's phone number input
@form_router.message(Form.edit_phone)
async def process_edit_phone(message: Message, state: FSMContext):
    phone_number = message.contact.phone_number
    await state.update_data(phone=phone_number)
    await state.set_state(Form.edit_role)
    role = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🚖 Driver', callback_data=MyCallback(name="driver_edit", id="1").pack()),
         InlineKeyboardButton(text='👤 Passenger', callback_data=MyCallback(name="passenger_edit", id="2").pack())],
    ])
    await message.answer("Got it! Are you a driver or passenger?\nPlease, choose your role.", reply_markup=role)

# DRIVER EDIT: CALLBACK QUERY
@form_router.callback_query(MyCallback.filter(F.name == "driver_edit"))
async def callback_process_driver_edit(query: types.CallbackQuery, callback_data: MyCallback, state: FSMContext):
    await process_driver_role(query, callback_data, state, edit_mode=True)

# PASSENGER EDIT: CALLBACK QUERY
@form_router.callback_query(MyCallback.filter(F.name == "passenger_edit"))
async def callback_process_passenger_edit(query: types.CallbackQuery, callback_data: MyCallback, state: FSMContext):
    await process_passenger_role(query, callback_data, state, edit_mode=True)

# ... Continue this pattern for other functions/handlers ...

# MAIN: RUN
async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(form_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
