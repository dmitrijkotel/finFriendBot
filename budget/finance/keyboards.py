from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

back_income_categories_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_income_categories_button')]
])

skip_description_income_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⏭️ Пропустить', callback_data='skip_income_categories_button')],
    [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_description_income_button')],
])

back_expenses_categories_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔙 Вернуться назад', callback_data='back_expenses_categories_button')]
])

continue_expenses_categories_keyboards = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='➡️ Продолжить', callback_data='continue_expenses_categories_button')]
])

continue_income_categories_keyboards = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='➡️ Продолжить', callback_data='continue_income_categories_button')]
])

skip_description_expenses_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⏭️ Пропустить', callback_data='skip_expenses_categories_button')],
    [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_description_expenses_button')],
])

back_create_transactions_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='back_create_transactions_button')]
])
