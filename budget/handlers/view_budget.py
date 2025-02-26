from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
import aiosqlite

# Импортируем необходимые функции из других модулей
from budget.database import get_budget_details_db
from budget.database import get_budgets_from_db

from budget.functions import (
    edit_name_budget_function, edit_description_budget_function,delete_budget_function, edit_budget_function,
    process_edit_budget_description_function, process_edit_budget_name_function
)

from budget.keyboards import back_menu, cancel_sure_keyboard
from budget.functions import create_keyboard

# Создаем роутер
view_budget_router = Router()

# Функции для работы с базой данных
async def get_total_income_by_budget(budget_id: int):
    async with aiosqlite.connect('database.db') as conn:
        async with conn.execute(
            """
            SELECT SUM(t.amount) 
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE c.budget_id = ? AND c.type = 'income'
            """,
            (budget_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result[0] is not None else 0

async def get_total_expense_by_budget(budget_id: int):
    async with aiosqlite.connect('database.db') as conn:
        async with conn.execute(
            """
            SELECT SUM(t.amount) 
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE c.budget_id = ? AND c.type = 'expense'
            """,
            (budget_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result[0] is not None else 0

# Функция для создания клавиатуры с суммами доходов и расходов
async def create_actions_budget_keyboard(budget_id: int):
    total_income = await get_total_income_by_budget(budget_id)
    total_expense = await get_total_expense_by_budget(budget_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f'Расходы ({total_expense}₽)', callback_data='expenses_budget_button'),
            InlineKeyboardButton(text=f'Доходы ({total_income}₽)', callback_data='income_budget_button')
        ],
        [
            InlineKeyboardButton(text='Удалить', callback_data='delete_budget_button'),
            InlineKeyboardButton(text='Изменить', callback_data='edit_budget_button')
        ],
        [
            InlineKeyboardButton(text='Oтчёт', callback_data='report_budget_button')
        ],
        [
            InlineKeyboardButton(text='Назад', callback_data='back_menu_budget_button')
        ],
    ])
    return keyboard

# Функция для отображения меню бюджетов
async def menu_budgets(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    await callback.answer()

    budgets = await get_budgets_from_db(telegram_id)

    if not budgets:
        return await callback.message.edit_text("Нет доступных бюджетов.", reply_markup=back_menu)

    keyboard = await create_keyboard(budgets)
    await callback.message.edit_text("Выберите бюджет:", reply_markup=keyboard)

# Состояния для редактирования бюджета
class EditBudgetStates(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_budget_new_description = State()

# Обработчик для просмотра бюджетов
@view_budget_router.callback_query(F.data == 'view_budget_button')
async def view_budget_handler(callback: CallbackQuery):
    await menu_budgets(callback)
    await callback.answer()

# Обработчик для выбора бюджета
@view_budget_router.callback_query(lambda call: call.data.isdigit())
async def handle_budget_selection(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        budget_id = int(callback.data)
        await state.update_data(budget_id=budget_id)  # Сохраняем budget_id в состоянии

        budget_details = await get_budget_details_db(budget_id)
        if budget_details:
            budget_name, description = budget_details
            response_message = f"{budget_name}\nОписание: {description}" if description else f"{budget_name}\n__________________________________________"
        else:
            response_message = "Бюджет не найден."

        keyboard = await create_actions_budget_keyboard(budget_id)
        await callback.message.edit_text(response_message, reply_markup=keyboard)
    except Exception as e:
        await callback.answer("Произошла ошибка. Попробуйте позже.")
        print(f"Ошибка при обработке запроса: {e}")

# Обработчики для удаления бюджета
@view_budget_router.callback_query(F.data == 'delete_budget_button')
async def delete_budget_handler(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text('Вы уверены, что хотите удалить этот бюджет?', reply_markup=cancel_sure_keyboard)

@view_budget_router.callback_query(F.data == 'yes_button')
async def confirm_delete_budget_handler(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')  # Получаем budget_id из состояния
    await delete_budget_function(callback, budget_id)

@view_budget_router.callback_query(F.data == 'back_button_sure')
async def cancel_delete_budget_handler(callback: CallbackQuery):
    await menu_budgets(callback)

# Обработчики для возврата в меню
@view_budget_router.callback_query(F.data == 'back_menu_budget_button')
async def back_to_menu_handler(callback: CallbackQuery):
    await menu_budgets(callback)

# Обработчики для редактирования бюджета
@view_budget_router.callback_query(F.data == 'edit_budget_button')
async def edit_budget_handler(callback: CallbackQuery):
    await edit_budget_function(callback)

@view_budget_router.callback_query(F.data == 'back_edit_budget_button')
async def cancel_edit_budget_handler(callback: CallbackQuery):
    await menu_budgets(callback)

# Обработчики для редактирования имени бюджета
@view_budget_router.callback_query(F.data == 'edit_name_budget_button')
async def edit_name_budget_handler(callback: CallbackQuery, state: FSMContext):
    await edit_name_budget_function(callback, state, EditBudgetStates)

@view_budget_router.message(EditBudgetStates.waiting_for_new_name)
async def process_update_budget_name_handler(message: Message, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')  # Получаем budget_id из состояния
    await process_edit_budget_name_function(message, state, budget_id)

# Обработчики для редактирования описания бюджета
@view_budget_router.callback_query(F.data == 'edit_description_button')
async def edit_description_budget_handler(callback: CallbackQuery, state: FSMContext):
    await edit_description_budget_function(callback, state, EditBudgetStates)

@view_budget_router.message(EditBudgetStates.waiting_for_budget_new_description)
async def process_edit_budget_description_handler(message: Message, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')  # Получаем budget_id из состояния
    await process_edit_budget_description_function(message, state, budget_id)

@view_budget_router.callback_query(F.data == 'back_button_complete_delete')
async def create_budget(callback: CallbackQuery):
    await menu_budgets(callback)

@view_budget_router.callback_query(F.data == 'back_edit_name_budget_button')
async def create_budget(callback: CallbackQuery):
    await menu_budgets(callback)