# modules/rating_reviews.py
from aiogram import types
from my_callback import MyCallback

async def process_rate(query: types.CallbackQuery, callback_data: MyCallback):
    # Handle rating
    pass

async def process_rate_passenger(query: types.CallbackQuery, callback_data: MyCallback):
    # Handle rating for passenger
    pass

async def process_star(query: types.CallbackQuery, callback_data: MyCallback):
    # Handle star rating
    pass
