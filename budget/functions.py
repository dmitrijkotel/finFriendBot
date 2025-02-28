from aiogram.types import CallbackQuery
from budget.keyboards import edit_budget_keyboard
from budget.database import delete_budget_db

async def delete_budget_function(callback: CallbackQuery, budget_id):
    if budget_id is None:
        await callback.message.edit_text("Выберите бюджет для удаления.", show_alert=True)
        return
    
    await callback.answer()

    # Удаляем бюджет по ID
    await delete_budget_db(budget_id, callback.message)  # Теперь передаем бюджет_id
    budget_id = None  # Сбрасываем budget_id после операции


async def edit_budget_function(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text('Что желаете изменить?', reply_markup=edit_budget_keyboard)  # Отправляем сообщение с деталями бюджета

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

async def create_keyboard(budgets):
    keyboard = InlineKeyboardBuilder()
    back = InlineKeyboardButton(text="Назад", callback_data="back_button")

    for budget_id, budget_name in budgets:
        button = InlineKeyboardButton(text=budget_name, callback_data=str(budget_id))
        keyboard.add(button)  # Добавляем кнопку в клавиатуру

    keyboard.add(back)
    return keyboard.adjust(1).as_markup()  # Настраиваем клавиатуру на 2 кнопки в строке

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from budget.keyboards import back_edit_name_budget_keyboard, back_complete_edit_name_keyboard
from budget.database import set_new_budget_description
from budget.database import set_new_budget_name

async def edit_name_budget_function(callback: CallbackQuery, state: FSMContext, edit_budget_states):
        # Отправляем сообщение с просьбой ввести название бюджета и сохраняем идентификатор
        bot_message = await callback.message.edit_text("Введите название для бюджета:", reply_markup=back_edit_name_budget_keyboard)
        await state.update_data(bot_message_id=bot_message.message_id)
        await state.set_state(edit_budget_states.waiting_for_new_name)
        await callback.answer()

async def process_edit_budget_name_function(message: Message, state: FSMContext, budget_id):
    budget_name = message.text
    await state.update_data(budget_name=budget_name)  # Сохраняем название бюджета в состоянии
    await message.delete()  # Удаляем сообщение пользователя

    # Получаем идентификатор сообщения бота и удаляем его
    user_data = await state.get_data()
    bot_message_id = user_data.get('bot_message_id')
    await message.bot.delete_message(chat_id=message.chat.id, message_id=bot_message_id)
    await set_new_budget_name(message, budget_name, budget_id)
    await state.clear()  # Очистка состояния


async def edit_description_budget_function(callback: CallbackQuery, state: FSMContext, edit_budget_states):

    # Отправляем сообщение и сохраняем идентификатор сообщения
    bot_message = await callback.message.edit_text("Введите описание для бюджета:", reply_markup=back_edit_description_budget_keyboard)
    await state.update_data(bot_message_id=bot_message.message_id)

    await state.set_state(edit_budget_states.waiting_for_budget_new_description)
    await callback.answer()

from budget.keyboards import back_edit_description_budget_keyboard

async def process_edit_budget_description_function(message: Message, state: FSMContext, budget_id):
    budget_description = message.text
    await state.update_data(budget_name=budget_description)  # Сохраняем новое описание бюджета
    await message.delete()  # Удаляем сообщение пользователя

    # Получаем идентификатор сообщения бота и редактируем его
    user_data = await state.get_data()
    bot_message_id = user_data.get('bot_message_id')

    # Убедимся, что budget_id установлен перед вызовом функции обновления
    if budget_id is not None:
        await set_new_budget_description(message, budget_description, budget_id, bot_message_id)
    else:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="Не удалось получить идентификатор бюджета. Обновление невозможно.",
            reply_markup=back_edit_description_budget_keyboard
        )
    await state.clear()  # Очистка состояния