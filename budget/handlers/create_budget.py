import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from budget.keyboards import (
    budget_menu_keyboard, back_keyboard, add_budget_description_keyboard
)
from budget.database import delete_budget_db, set_new_budget_name, set_new_budget_description, add_budget_db
from aiogram.fsm.state import State, StatesGroup

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

create_budget_router = Router()

class create_budget_states(StatesGroup):
    waiting_for_budget_title = State()
    waiting_for_budget_description = State()

@create_budget_router.callback_query(F.data == 'create_budget_button')
async def create_budget_handler(callback: CallbackQuery, state: FSMContext):
    logger.info("Пользователь %s начал создание бюджета", callback.from_user.id)
    bot_message = await callback.message.edit_text("📝 Введите название для бюджета:", reply_markup=back_keyboard)
    await state.update_data(bot_message_id=bot_message.message_id)
    await state.set_state(create_budget_states.waiting_for_budget_title)
    await callback.answer()

@create_budget_router.message(create_budget_states.waiting_for_budget_title)
async def create_budget_name(message: Message, state: FSMContext):
    budget_name = message.text
    logger.info("Пользователь %s ввел название бюджета: '%s'", message.from_user.id, budget_name)
    await state.update_data(budget_name=budget_name)
    await message.delete()

    user_data = await state.get_data()
    bot_message_id = user_data.get('bot_message_id')
    
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=bot_message_id,
        text="📝 Введите описание бюджета:",
        reply_markup=add_budget_description_keyboard
    )
    await state.set_state(create_budget_states.waiting_for_budget_description)

@create_budget_router.message(create_budget_states.waiting_for_budget_description)
async def create_budget_description(message: Message, state: FSMContext):
    user_data = await state.get_data()
    bot_message_id = user_data.get('bot_message_id')
    description = message.text if message.text else ''
    
    logger.info("Пользователь %s ввел описание бюджета: '%s'", message.from_user.id, description)
    await state.update_data(description=description)
    await message.delete()

    budget_name = user_data.get('budget_name')
    telegram_id = message.from_user.id
    result = add_budget_db(telegram_id, budget_name, description)

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=bot_message_id,
        text=result,
        reply_markup=budget_menu_keyboard
    )
    await state.clear()

@create_budget_router.callback_query(F.data == 'skip_budget_description_button')
async def skip_button(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_data = await state.get_data()
    budget_name = user_data.get('budget_name')
    description = ''
    
    logger.info("Пользователь %s пропустил ввод описания бюджета", callback.from_user.id)
    await state.update_data(description=description)
    telegram_id = callback.from_user.id
    result = add_budget_db(telegram_id, budget_name, description)

    await callback.message.edit_text(result, reply_markup=budget_menu_keyboard)
    await state.clear()