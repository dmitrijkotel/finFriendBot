from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

report_format_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📊 Excel', callback_data='excel_report_format_button')],
    [InlineKeyboardButton(text='🖼️ JPEG', callback_data='jpeg_report_format_button')],
    [InlineKeyboardButton(text='📄 PDF', callback_data='pdf_report_format_button')],
    [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_report_button')]
])

back_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔙 Вернуться назад', callback_data='back_menu_button')]
])
