from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from start.keyboards import registration_keyboard
from budget.keyboards import budget_menu_keyboard
from start.database import registration

registration_router = Router()

async def start_message(message):

    await message.answer('Пожалуйста, пройдите регистрацию, чтобы открыть все его возможности!', reply_markup = registration_keyboard)

@registration_router.callback_query(F.data == 'reg')
async def create_budget(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text('Управление бюджетом', reply_markup=budget_menu_keyboard)

# Обработчик команды /start
@registration_router.message(CommandStart())
async def start(message: Message):

        telegram_id = message.from_user.id
        result = registration(telegram_id)
        if result == 0:
            await start_message(message)
        else:
            await message.answer('Управление бюджетом', reply_markup=budget_menu_keyboard)