from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from budget.keyboards import (
    edit_budget_keyboard, back_edit_name_budget_keyboard,
    back_edit_description_budget_keyboard, back_complete_edit_name_keyboard
)
from budget.database import delete_budget_db, set_new_budget_name, set_new_budget_description


async def delete_budget_function(callback: CallbackQuery, budget_id):
    if budget_id is None:
        await callback.answer("Выберите бюджет для удаления.", show_alert=True)
        return

    await callback.answer()
    await delete_budget_db(budget_id, callback.message)  # Удаляем бюджет


async def edit_budget_function(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Что желаете изменить?", reply_markup=edit_budget_keyboard)


async def create_keyboard(budgets):
    keyboard = InlineKeyboardBuilder()
    back = InlineKeyboardButton(text="🔙 Назад", callback_data="back_button")

    for budget_id, budget_name in budgets:
        button = InlineKeyboardButton(text=budget_name, callback_data=str(budget_id))
        keyboard.add(button)

    keyboard.add(back)
    return keyboard.adjust(1).as_markup()  # Каждая кнопка в отдельной строке


async def edit_name_budget_function(callback: CallbackQuery, state: FSMContext, edit_budget_states):
    bot_message = await callback.message.edit_text("✏️ Введите новое название бюджета:", reply_markup=back_edit_name_budget_keyboard)
    await state.update_data(bot_message_id=bot_message.message_id)
    await state.set_state(edit_budget_states.waiting_for_new_name)
    await callback.answer()


async def process_edit_budget_name_function(message: Message, state: FSMContext, budget_id):
    budget_name = message.text
    await state.update_data(budget_name=budget_name)  # Сохраняем новое название
    await message.delete()  # Удаляем сообщение пользователя

    # Удаляем старое сообщение бота
    user_data = await state.get_data()
    bot_message_id = user_data.get("bot_message_id")
    await message.bot.delete_message(chat_id=message.chat.id, message_id=bot_message_id)

    await set_new_budget_name(message, budget_name, budget_id)
    await state.clear()  # Очистка состояния


async def edit_description_budget_function(callback: CallbackQuery, state: FSMContext, edit_budget_states):
    bot_message = await callback.message.edit_text("📝 Введите новое описание бюджета:", reply_markup=back_edit_description_budget_keyboard)
    await state.update_data(bot_message_id=bot_message.message_id)
    await state.set_state(edit_budget_states.waiting_for_budget_new_description)
    await callback.answer()


async def process_edit_budget_description_function(message: Message, state: FSMContext, budget_id):
    budget_description = message.text
    await state.update_data(budget_description=budget_description)  # Исправлено
    await message.delete()  # Удаляем сообщение пользователя

    # Получаем ID предыдущего сообщения бота
    user_data = await state.get_data()
    bot_message_id = user_data.get("bot_message_id")

    if budget_id is not None:
        await set_new_budget_description(message, budget_description, budget_id, bot_message_id)
    else:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="❌ Ошибка: не удалось получить идентификатор бюджета. Описание не обновлено.",
            reply_markup=back_edit_description_budget_keyboard
        )

    await state.clear()  # Очистка состояния