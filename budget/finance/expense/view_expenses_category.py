import logging
from typing import Union
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
import aiosqlite
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from budget.database import get_budget_details_db, get_budgets_from_db
from budget.functions import create_keyboard
from budget.handlers.view_budget import create_actions_budget_keyboard, get_total_expense_by_budget, get_total_income_by_budget
from budget.keyboards import back_menu

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

view_expenses_category_router = Router()

async def get_expenses_categories_from_db(budget_id: int):
    logger.info(f"Получение категорий расходов для бюджета {budget_id}")
    async with aiosqlite.connect('database.db') as conn:
        async with conn.execute(
            "SELECT id, name FROM categories WHERE budget_id = ? AND type = ?",
            (budget_id, 'expense')
        ) as cursor:
            return await cursor.fetchall()
        
async def get_transactions_sum_by_category(category_id: int):
    logger.info(f"Получение суммы транзакций для категории {category_id}")
    async with aiosqlite.connect('database.db') as conn:
        async with conn.execute(
            "SELECT SUM(amount) FROM transactions WHERE category_id = ?",
            (category_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result[0] is not None else 0

async def create_expenses_categories_keyboard(categories):
    keyboard = InlineKeyboardBuilder()
    for category_id, category_name in categories:
        transactions_sum = await get_transactions_sum_by_category(category_id)
        button_text = f"📂 {category_name} ({transactions_sum}₽)"
        button = InlineKeyboardButton(text=button_text, callback_data=f"category_income_{category_id}")
        keyboard.add(button)
        keyboard.adjust(1)
    keyboard.row(
        InlineKeyboardButton(text="➕ Добавить", callback_data="add_expenses_category_button"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_expenses_categories_button")
    )
    return keyboard.as_markup()

async def view_expenses_categories(message: Message, budget_id: int):
    logger.info(f"Просмотр категорий расходов для бюджета {budget_id}")
    categories = await get_expenses_categories_from_db(budget_id)
    keyboard = await create_expenses_categories_keyboard(categories)
    text = "📂 Нет доступных категорий расходов." if not categories else "📂 Выберите категорию расхода:"
    await message.edit_text(text, reply_markup=keyboard)

async def menu_budgets(callback):
    telegram_id = callback.from_user.id
    logger.info(f"Просмотр бюджетов для пользователя {telegram_id}")
    await callback.answer()
    budgets = await get_budgets_from_db(telegram_id)
    if not budgets:
        return await callback.message.answer("📂 Нет доступных бюджетов.", reply_markup=back_menu)
    keyboard = await create_keyboard(budgets)
    await callback.message.edit_text("📂 Выберите бюджет:", reply_markup=keyboard)

@view_expenses_category_router.callback_query(F.data == 'back_expenses_categories_button')
async def back_button_handler(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')
    logger.info(f"Возврат в меню бюджета {budget_id}")
    await budget_menu_finance(callback, budget_id)

@view_expenses_category_router.callback_query(F.data == 'expenses_budget_button')
async def view_expenses_categories_handler(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')
    if budget_id is None:
        await callback.answer("❌ Ошибка: идентификатор бюджета не найден.")
        logger.error("Ошибка: идентификатор бюджета не найден.")
        return
    await view_expenses_categories(callback.message, budget_id)

async def get_category_details_db(category_id: int):
    logger.info(f"Получение данных о категории {category_id}")
    async with aiosqlite.connect('database.db') as db:
        async with db.execute("SELECT name, description FROM categories WHERE id = ?", (category_id,)) as cursor:
            return await cursor.fetchone()

income_category_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔙 Назад', callback_data='back_from_all_expenses_categories_button')]
])

@view_expenses_category_router.callback_query(F.data == 'back_from_all_expenses_categories_button')
async def back_from_all_expenses_categories_handler(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')
    if budget_id is None:
        await callback.answer("❌ Ошибка: идентификатор бюджета не найден.")
        logger.error("Ошибка: идентификатор бюджета не найден.")
        return
    await callback.message.delete()
    await view_expenses_categories(callback.message, budget_id)

async def budget_menu_finance(event: Union[Message, CallbackQuery], budget_id):
    try:
        logger.info(f"Формирование меню бюджета {budget_id}")
        total_income = await get_total_income_by_budget(budget_id)
        total_expense = await get_total_expense_by_budget(budget_id)
        balance = total_income - total_expense
        budget_details = await get_budget_details_db(budget_id)
        if budget_details:
            budget_name, description = budget_details
            response_message = f"📋 Название: {budget_name}\n💰 Баланс: {balance}₽" if not description else f"📋 Название: {budget_name}\n📝 Описание: {description}\n💰 Баланс: {balance}₽"
        else:
            response_message = "❌ Бюджет не найден."
        keyboard = await create_actions_budget_keyboard(budget_id)
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(response_message, reply_markup=keyboard)
        else:
            await event.answer(response_message, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        if isinstance(event, CallbackQuery):
            await event.answer("❌ Произошла ошибка. Попробуйте позже.")