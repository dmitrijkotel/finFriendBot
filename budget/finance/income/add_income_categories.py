import sqlite3
import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from budget.finance.keyboards import back_income_categories_keyboard as kb_back
from budget.handlers.view_budget import budget_menu_finance

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

create_income_category_router = Router()

class CreateIncomeCategoryStates(StatesGroup):
    waiting_for_category_title = State()
    stop = State()

budget_id_g = 0

def add_income_category_db(budget_id, category_name):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        cursor.execute("""  
            INSERT INTO categories (budget_id, name, type)   
            VALUES (?, ?, 'income')""",
                       (budget_id, category_name))
        conn.commit()
        logger.info(f"Категория '{category_name}' добавлена в БД для budget_id {budget_id}")
        return "✅ Категория дохода успешно добавлена!"
    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при добавлении категории: {e}")
        return f"❌ Произошла ошибка: {str(e)}"
    finally:
        cursor.close()
        conn.close()

@create_income_category_router.callback_query(F.data == 'add_income_category_button')
async def create_income_category_handler(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')
    logger.info(f"Создание категории: budget_id = {budget_id}")

    if not budget_id:
        await callback.answer("❌ Ошибка: идентификатор бюджета не найден.")
        logger.error("Ошибка: идентификатор бюджета не найден.")
        return

    bot_message = await callback.message.edit_text("📝 Введите название для категории дохода:", reply_markup=kb_back)
    await state.update_data(bot_message_id=bot_message.message_id, budget_id=budget_id)
    global budget_id_g
    budget_id_g = budget_id
    await state.set_state(CreateIncomeCategoryStates.waiting_for_category_title)
    await callback.answer()

@create_income_category_router.message(CreateIncomeCategoryStates.waiting_for_category_title)
async def create_income_category_name(message: Message, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    category_name = message.text
    await state.update_data(category_name=category_name)
    logger.info(f"Пользователь ввел название категории: {category_name}")

    await message.delete()
    user_data = await state.get_data()
    bot_message_id = user_data.get('bot_message_id')

    result = add_income_category_db(budget_id, category_name)
    await state.set_state(CreateIncomeCategoryStates.stop)

    if bot_message_id:
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=bot_message_id,
                text=result,
                reply_markup=kb_back
            )
            await budget_menu_finance(message, budget_id, bot_message_id)
        except Exception as e:
            logger.error(f"Ошибка при редактировании сообщения: {e}")
    else:
        sent_message = await budget_menu_finance(message, budget_id)
        await state.update_data(bot_message_id=sent_message.message_id)