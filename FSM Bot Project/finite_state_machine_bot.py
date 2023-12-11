
import asyncio
import logging
import sys
from os import getenv
from dotenv import load_dotenv
from typing import Any, Dict

from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
# Load environment variables from the .env file
load_dotenv()
TOKEN = getenv("TOKEN")

form_router = Router()


class Form(StatesGroup):
    name = State()
    gender = State()
    department = State()
    school = State()


@form_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.name)
    await message.answer(
        "Hello! Welcome to Registration System. Please enter your name to register.",
        reply_markup = ReplyKeyboardRemove(),
    )


@form_router.message(Command("cancel"))
@form_router.message(F.text.casefold() == "cancel")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    await state.clear()
    await message.answer(
        "Cancelled.",
        reply_markup=ReplyKeyboardRemove(),
    )


@form_router.message(Form.name)
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(Form.gender)
    await message.answer(
        f"Welcome, {html.quote(message.text)}!\nPlease choose your gender",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Male"),
                    KeyboardButton(text="Female"),
                    KeyboardButton(text="Cancel"),
                ]
            ],
            resize_keyboard=True,
        ),
    )


@form_router.message(Form.gender)
async def process_gender(message: Message, state: FSMContext) -> None:
    if message.text.casefold() == "cancel":
        await cancel_handler(message, state)
        return

    await state.update_data(gender=message.text)
    await state.set_state(Form.department)
    await message.answer(
        f"What department did you study in?",
        reply_markup=ReplyKeyboardRemove(),
    )


@form_router.message(Form.department)
async def process_department(message: Message, state: FSMContext) -> None:
    data = await state.update_data(department=message.text)

    if message.text.casefold() == "software engineering":
        await state.set_state(Form.school)
        await message.reply(
            "Nice choice! What university did you study at?",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        await show_summary(message=message, data=data)
        await state.finish()


@form_router.message(Form.school)
async def process_school(message: Message, state: FSMContext) -> None:
    data = await state.update_data(school=message.text)
    await show_summary(message=message, data=data)
    await state.finish()


async def show_summary(message: Message, data: Dict[str, Any]) -> None:
    name = data["name"]
    gender = data["gender"]
    department = data["department"]
    school = data.get("school", "N/A")

    text = f"Registration Summary:\n"
    text += f"Name: {html.quote(name)}\n"
    text += f"Gender: {gender}\n"
    text += f"Department: {html.quote(department)}\n"
    text += f"School: {html.quote(school)}\n"

    await message.answer(text, reply_markup=ReplyKeyboardRemove())


async def main():
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(form_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())