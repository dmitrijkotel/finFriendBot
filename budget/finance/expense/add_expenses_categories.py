import sqlite3
import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from budget.handlers.view_budget import budget_menu_finance
from budget.finance.keyboards import back_expenses_categories_keyboard as kb_back

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

create_expenses_category_router = Router()

class CreateExpenseCategoryStates(StatesGroup):
    waiting_for_expenses_category_title = State()
    stop = State()

budget_id_g = 0

def add_expenses_category_db(budget_id, category_name):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        cursor.execute("""  
            INSERT INTO categories (budget_id, name, type)   
            VALUES (?, ?, 'expense')""",
                       (budget_id, category_name))
        conn.commit()
        logger.info(f"Категория расхода '{category_name}' добавлена в бюджет ID {budget_id}")
        return "✅ Категория расхода успешно добавлена!"
    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при добавлении категории расхода: {e}")
        return f"❌ Произошла ошибка: {str(e)}"
    finally:
        cursor.close()
        conn.close()

@create_expenses_category_router.callback_query(F.data == 'add_expenses_category_button')
async def create_expenses_category_handler(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')
    logger.info(f"Запрос на создание категории расходов. budget_id = {budget_id}")

    if not budget_id:
        await callback.answer("❌ Ошибка: идентификатор бюджета не найден.")
        return

    bot_message = await callback.message.edit_text("📝 Введите название для категории расхода:", reply_markup=kb_back)
    await state.update_data(bot_message_id=bot_message.message_id, budget_id=budget_id)
    global budget_id_g
    budget_id_g = budget_id
    await state.set_state(CreateExpenseCategoryStates.waiting_for_expenses_category_title)
    await callback.answer()

@create_expenses_category_router.message(CreateExpenseCategoryStates.waiting_for_expenses_category_title)
async def create_expenses_category_name(message: Message, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    category_name = message.text
    await state.update_data(category_name=category_name)
    logger.info(f"Пользователь ввел название категории: {category_name}")

    await message.delete()  # Удаляем сообщение пользователя

    user_data = await state.get_data()
    bot_message_id = user_data.get('bot_message_id')

    # Добавляем категорию в БД
    result = add_expenses_category_db(budget_id, category_name)

    await state.set_state(CreateExpenseCategoryStates.stop)

    # Если у нас есть ID сообщения, редактируем его
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
        # Если нет сохранённого ID, отправляем новое меню и запоминаем его
        sent_message = await budget_menu_finance(message, budget_id)
        await state.update_data(bot_message_id=sent_message.message_id)