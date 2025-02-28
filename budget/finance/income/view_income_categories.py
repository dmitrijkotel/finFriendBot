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

view_income_category_router = Router()

async def get_income_categories_from_db(budget_id: int):
    async with aiosqlite.connect('database.db') as conn:
        async with conn.execute(
            "SELECT id, name FROM categories WHERE budget_id = ? AND type = ?",
            (budget_id, 'income')
        ) as cursor:
            return await cursor.fetchall()
        
async def get_transactions_sum_by_category(category_id: int):
    async with aiosqlite.connect('database.db') as conn:
        async with conn.execute(
            "SELECT SUM(amount) FROM transactions WHERE category_id = ?",
            (category_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result[0] is not None else 0

async def create_income_categories_keyboard(categories):
    keyboard = InlineKeyboardBuilder()

    # Создаем кнопки для каждой категории
    for category_id, category_name in categories:
        # Получаем сумму транзакций для категории
        transactions_sum = await get_transactions_sum_by_category(category_id)
        
        # Формируем текст кнопки с названием категории и суммой транзакций
        button_text = f"{category_name} ({transactions_sum}₽)"
        
        # Создаем кнопку
        button = InlineKeyboardButton(text=button_text, callback_data=f"category_income_{category_id}")
        keyboard.add(button)
        
    keyboard.adjust(1)  # 1 кнопка в ряд

    # Добавить кнопки "Добавить категорию" и "Назад" в новую строку
    keyboard.row(
        InlineKeyboardButton(text="Добавить", callback_data="add_income_category_button"),
        InlineKeyboardButton(text="Назад", callback_data="back_income_categories_button")
    )

    # Возвращаем клавиатуру
    return keyboard.as_markup()

async def view_income_categories(message: Message, budget_id: int):
    categories = await get_income_categories_from_db(budget_id)
    keyboard = await create_income_categories_keyboard(categories)

    if not categories:
        await message.edit_text("Нет доступных категорий доходов.", reply_markup=keyboard)
    else:
        await message.edit_text("Выберите категорию дохода:", reply_markup=keyboard)

@view_income_category_router.callback_query(F.data == 'back_income_categories_button')
async def back_button_handler(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    await budget_menu_finance(callback, budget_id)

@view_income_category_router.callback_query(F.data == 'income_budget_button')
async def view_income_categories_handler(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    if budget_id is None:
        await callback.answer("Ошибка: идентификатор бюджета не найден.")
        return

    await view_income_categories(callback.message, budget_id)

async def get_category_details_db(category_id: int):
    async with aiosqlite.connect('tgBotDb.db') as db:
        async with db.execute("SELECT name, description FROM categories WHERE id = ?", (category_id,)) as cursor:
            return await cursor.fetchone()

income_category_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад', callback_data='back_from_all_income_categories_button')]
])

@view_income_category_router.callback_query(F.data == 'back_from_all_income_categories_button')
async def back_from_all_income_categories_handler(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    if budget_id is None:
        await callback.answer("Ошибка: идентификатор бюджета не найден.")
        return

    await callback.message.delete()
    await view_income_categories(callback.message, budget_id)

