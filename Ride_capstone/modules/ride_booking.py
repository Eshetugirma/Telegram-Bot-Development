# modules/ride_booking.py
from aiogram import types, FSMContext
from my_callback import MyCallback
from aiogram.dispatcher import State, StatesGroup

class Form(StatesGroup):
    current_location = State()
    destination = State()

async def process_ride(query: types.CallbackQuery, callback_data: MyCallback, state: FSMContext):
    # Handle ride booking
    pass

async def process_current_location(message: types.Message, state: FSMContext):
    # Handle processing current location
    pass

async def process_destination(message: types.Message, state: FSMContext):
    # Handle processing destination
    pass
