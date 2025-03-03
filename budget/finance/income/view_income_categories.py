import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
import aiosqlite
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from budget.database import get_budgets_from_db 
from budget.finance.expense.view_expenses_category import budget_menu_finance
from budget.functions import create_keyboard
from budget.keyboards import back_menu

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

view_income_category_router = Router()

async def get_income_categories_from_db(budget_id: int):
    logging.info(f"Получение категорий доходов для бюджета ID {budget_id}")
    try:
        async with aiosqlite.connect('database.db') as conn:
            async with conn.execute(
                "SELECT id, name FROM categories WHERE budget_id = ? AND type = ?",
                (budget_id, 'income')
            ) as cursor:
                categories = await cursor.fetchall()
                logging.info(f"Найдено {len(categories)} категорий доходов")
                return categories
    except Exception as e:
        logging.error(f"Ошибка при получении категорий доходов: {e}")
        return []

async def get_transactions_sum_by_category(category_id: int):
    logging.info(f"Получение суммы транзакций для категории ID {category_id}")
    try:
        async with aiosqlite.connect('database.db') as conn:
            async with conn.execute(
                "SELECT SUM(amount) FROM transactions WHERE category_id = ?",
                (category_id,)
            ) as cursor:
                result = await cursor.fetchone()
                sum_value = result[0] if result[0] is not None else 0
                logging.info(f"Сумма транзакций для категории ID {category_id}: {sum_value}")
                return sum_value
    except Exception as e:
        logging.error(f"Ошибка при получении суммы транзакций: {e}")
        return 0

async def create_income_categories_keyboard(categories):
    logging.info("Создание клавиатуры категорий доходов")
    keyboard = InlineKeyboardBuilder()
    try:
        for category_id, category_name in categories:
            transactions_sum = await get_transactions_sum_by_category(category_id)
            button_text = f"\U0001F4C2 {category_name} ({transactions_sum}₽)"
            keyboard.add(InlineKeyboardButton(text=button_text, callback_data=f"category_income_{category_id}"))
        
        keyboard.adjust(1)
        keyboard.row(
            InlineKeyboardButton(text="➕ Добавить", callback_data="add_income_category_button"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_income_categories_button")
        )
        return keyboard.as_markup()
    except Exception as e:
        logging.error(f"Ошибка при создании клавиатуры: {e}")
        return InlineKeyboardMarkup(inline_keyboard=[])

async def view_income_categories(message: Message, budget_id: int):
    logging.info(f"Отображение категорий доходов для бюджета ID {budget_id}")
    categories = await get_income_categories_from_db(budget_id)
    keyboard = await create_income_categories_keyboard(categories)
    try:
        if not categories:
            await message.edit_text("📂 Нет доступных категорий доходов.", reply_markup=keyboard)
        else:
            await message.edit_text("📂 Выберите категорию дохода:", reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Ошибка при обновлении сообщения: {e}")

@view_income_category_router.callback_query(F.data == 'back_income_categories_button')
async def back_button_handler(callback: CallbackQuery, state: FSMContext):
    logging.info("Обработка нажатия кнопки 'Назад'")
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')
    await budget_menu_finance(callback, budget_id)

@view_income_category_router.callback_query(F.data == 'income_budget_button')
async def view_income_categories_handler(callback: CallbackQuery, state: FSMContext):
    logging.info("Обработка нажатия кнопки 'Просмотр категорий доходов'")
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')
    if budget_id is None:
        logging.warning("Ошибка: идентификатор бюджета не найден.")
        await callback.answer("❌ Ошибка: идентификатор бюджета не найден.")
        return
    await view_income_categories(callback.message, budget_id)

async def get_category_details_db(category_id: int):
    logging.info(f"Получение информации о категории ID {category_id}")
    try:
        async with aiosqlite.connect('tgBotDb.db') as db:
            async with db.execute("SELECT name, description FROM categories WHERE id = ?", (category_id,)) as cursor:
                return await cursor.fetchone()
    except Exception as e:
        logging.error(f"Ошибка при получении деталей категории: {e}")
        return None

income_category_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔙 Назад', callback_data='back_from_all_income_categories_button')]
])

@view_income_category_router.callback_query(F.data == 'back_from_all_income_categories_button')
async def back_from_all_income_categories_handler(callback: CallbackQuery, state: FSMContext):
    logging.info("Обработка нажатия кнопки 'Назад' из всех категорий доходов")
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')
    if budget_id is None:
        logging.warning("Ошибка: идентификатор бюджета не найден.")
        await callback.answer("❌ Ошибка: идентификатор бюджета не найден.")
        return
    await callback.message.delete()
    await view_income_categories(callback.message, budget_id)
