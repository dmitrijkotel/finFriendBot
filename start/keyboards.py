from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

registration_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Зарегистрироваться', callback_data='reg')]
])