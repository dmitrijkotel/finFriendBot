from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

budget_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📊 Создание бюджета', callback_data='create_budget_button')],
    [InlineKeyboardButton(text='👀 Просмотр бюджета', callback_data='view_budget_button')]
])

cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_button')],
])

back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_button')],
])

add_budget_description_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⏭️ Пропустить', callback_data='skip_budget_description_button')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_button')],
])

back_complete_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔙 Вернуться назад', callback_data='back_button_complete_delete')],
])

back_edit_name_budget_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='back_edit_name_budget_button')],
])

back_complete_edit_name_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔙 Вернуться назад', callback_data='back_menu_budget_button')],
])

back_complete_edit_description_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔙 Вернуться назад', callback_data='back_menu_budget_button')],
])

back_edit_description_budget_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='back_edit_description_budget_button')],
])

edit_budget_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📝 Название', callback_data='edit_name_budget_button')],
    [InlineKeyboardButton(text='🗒️ Описание', callback_data='edit_description_button')],
    [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_edit_budget_button')],
])

cancel_sure_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Да', callback_data='yes_button')],
    [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_button_sure')],
])

back_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_button')],
])
