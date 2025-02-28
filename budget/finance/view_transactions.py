from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
import aiosqlite
from datetime import datetime
import logging

from budget.database import get_budgets_from_db
from budget.functions import create_keyboard
from budget.handlers.view_budget import budget_menu_finance
from budget.keyboards import back_menu


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Константы
TRANSACTION_TYPE_EXPENSE = 'expense'
TRANSACTION_TYPE_INCOME = 'income'

# Роутер для обработки транзакций
view_transactions_router = Router()

# Состояния для добавления транзакций
class FormTransaction(StatesGroup):
    waiting_for_amount = State()
    waiting_for_description = State()
    stop = State()

# Функция для получения транзакций из базы данных
async def get_transactions_from_db(category_id: int, transaction_type: str):
    async with aiosqlite.connect('database.db') as conn:
        async with conn.execute(
            """SELECT id, amount, date 
               FROM transactions 
               WHERE category_id = ? AND type = ?
               ORDER BY date DESC""",
            (category_id, transaction_type)
        ) as cursor:
            return await cursor.fetchall()

# Функция для создания клавиатуры с транзакциями
async def create_transactions_keyboard(transactions: list, back_button_callback: str, add_button_callback: str, delete_button_callback: str):
    keyboard = InlineKeyboardBuilder()

    for transaction in transactions:
        trans_id, amount, date = transaction
        button_text = f"{date} - {amount}₽"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=f"transaction_{trans_id}"))

    keyboard.adjust(1)
    keyboard.row(
        InlineKeyboardButton(text="Назад", callback_data=back_button_callback),
        InlineKeyboardButton(text="Добавить", callback_data=add_button_callback),
        InlineKeyboardButton(text="Удалить", callback_data=delete_button_callback)
    )

    return keyboard.as_markup()

# Функция для отображения списка транзакций
async def view_transactions(message: Message, category_id: int, transaction_type: str, state: FSMContext):
    transactions = await get_transactions_from_db(category_id, transaction_type)
    keyboard = await create_transactions_keyboard(
        transactions,
        back_button_callback=f"back_{transaction_type}_transactions_button",
        add_button_callback=f"add_{transaction_type}_transaction_button",
        delete_button_callback=f"delete_{transaction_type}_category_button_{category_id}"
    )

    if not transactions:
        await message.edit_text(f"Нет транзакций в этой категории.", reply_markup=keyboard)
    else:
        await message.edit_text(f"Список транзакций ({'расходов' if transaction_type == TRANSACTION_TYPE_EXPENSE else 'доходов'}):", reply_markup=keyboard)

# Обработчик возврата в меню бюджетов
@view_transactions_router.callback_query(F.data.endswith('_transactions_button'))
async def back_to_categories_handler(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')
    await budget_menu_finance(callback.message, budget_id, callback.message.message_id)

# Обработчик выбора категории
@view_transactions_router.callback_query(F.data.startswith('category_'))
async def handle_category_selection(callback: CallbackQuery, state: FSMContext):
    try:
        data_parts = callback.data.split('_')
        transaction_type = data_parts[1]  # 'expense' или 'income'
        category_id = int(data_parts[2])

        await state.update_data(category_id=category_id, transaction_type=transaction_type)
        await view_transactions(callback.message, category_id, transaction_type, state)
    except (ValueError, IndexError) as e:
        await callback.answer("Ошибка загрузки транзакций")
        logger.error(f"Ошибка при выборе категории: {e}")

# Функция для получения деталей транзакции
async def get_transaction_details_db(transaction_id: int):
    async with aiosqlite.connect('database.db') as db:
        async with db.execute("""
            SELECT transactions.amount, transactions.date, transactions.description, categories.name
            FROM transactions
            JOIN categories ON transactions.category_id = categories.id
            WHERE transactions.id = ?
            """, (transaction_id,)) as cursor:
            return await cursor.fetchone()

# Функция для создания клавиатуры деталей транзакции
def create_transaction_detail_keyboard(transaction_id: int, back_button_callback: str):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data=back_button_callback))
    keyboard.add(InlineKeyboardButton(text='Удалить', callback_data=f'delete_transaction_{transaction_id}'))
    return keyboard.as_markup()

# Обработчик просмотра деталей транзакции
@view_transactions_router.callback_query(F.data.startswith('transaction_'))
async def show_transaction_detail(callback: CallbackQuery):
    transaction_id = int(callback.data.split('_')[1])
    transaction = await get_transaction_details_db(transaction_id)

    if transaction:
        amount, date, description, category = transaction
        response = (
            f"Категория: {category}\n"
            f"Сумма: {amount}₽\n"
            f"Дата: {date}\n"
            f"Описание: {description or 'нет описания'}"
        )
    else:
        response = "Транзакция не найдена"

    keyboard = create_transaction_detail_keyboard(transaction_id, back_button_callback='back_from_transaction_detail')
    await callback.message.edit_text(response, reply_markup=keyboard)
    await callback.answer()

# Обработчик удаления транзакции
@view_transactions_router.callback_query(F.data.startswith('delete_transaction_'))
async def delete_transaction_handler(callback: CallbackQuery):
    try:
        transaction_id = int(callback.data.split('_')[2])
        async with aiosqlite.connect('database.db') as conn:
            await conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            await conn.commit()

        await callback.message.edit_text("Транзакция успешно удалена.", reply_markup=create_return_keyboard())
    except (ValueError, IndexError, aiosqlite.Error) as e:
        await callback.answer("Ошибка: не удалось удалить транзакцию.")
        logger.error(f"Ошибка при удалении транзакции: {e}")
    await callback.answer()

# Обработчик удаления категории
@view_transactions_router.callback_query(F.data.startswith('delete_'))
async def delete_category_handler(callback: CallbackQuery):
    try:
        data_parts = callback.data.split('_')
        transaction_type = data_parts[1]  # 'expense' или 'income'
        category_id = int(data_parts[4])

        async with aiosqlite.connect('database.db') as conn:
            # Удаляем все транзакции в этой категории
            await conn.execute("DELETE FROM transactions WHERE category_id = ? AND type = ?", (category_id, transaction_type))
            # Удаляем саму категорию
            await conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            await conn.commit()

        await callback.message.edit_text(f"Категория и все связанные транзакции успешно удалены.", reply_markup=create_return_keyboard())
    except (ValueError, IndexError, aiosqlite.Error) as e:
        await callback.answer("Ошибка: не удалось удалить категорию.")
        logger.error(f"Ошибка при удалении категории: {e}")
    await callback.answer()

# Обработчик добавления транзакции
@view_transactions_router.callback_query(F.data.startswith('add_'))
async def add_transaction_handler(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    category_id = user_data.get('category_id')
    transaction_type = user_data.get('transaction_type')

    if category_id is None or transaction_type is None:
        await callback.answer("Ошибка: идентификатор категории или тип транзакции не найден.", show_alert=True)
        return

    bot_message = await callback.message.edit_text("Введите сумму транзакции:")
    await state.update_data(bot_message_id=bot_message.message_id, category_id=category_id, transaction_type=transaction_type)
    await state.set_state(FormTransaction.waiting_for_amount)
    await callback.answer()

# Обработчик ввода суммы транзакции
@view_transactions_router.message(FormTransaction.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    user_data = await state.get_data()
    await message.delete()

    try:
        amount = float(message.text)
        await state.update_data(amount=amount)

        bot_message_id = user_data.get('bot_message_id')
        if bot_message_id is not None:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=bot_message_id,
                text="Введите описание транзакции:"
            )

        await state.set_state(FormTransaction.waiting_for_description)

    except ValueError:
        bot_message_id = user_data.get('bot_message_id')
        if bot_message_id is not None:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=bot_message_id,
                text="Пожалуйста, введите корректную сумму."
            )

# Обработчик ввода описания транзакции
@view_transactions_router.message(FormTransaction.waiting_for_description)
async def create_transaction_description(message: Message, state: FSMContext):
    await message.delete()
    user_data = await state.get_data()
    amount = user_data.get('amount')
    category_id = user_data.get('category_id')
    transaction_type = user_data.get('transaction_type')
    description = message.text or ''
    transaction_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    bot_message_id = user_data.get('bot_message_id')
    if bot_message_id is not None:
        try:
            logger.info(f"Добавляем транзакцию: amount={amount}, description={description}, category_id={category_id}, date={transaction_date}, type={transaction_type}")
            async with aiosqlite.connect('database.db') as conn:
                await conn.execute(
                    """INSERT INTO transactions (amount, description, category_id, date, type)
                    VALUES (?, ?, ?, ?, ?)""",
                    (amount, description, category_id, transaction_date, transaction_type)
                )
                await conn.commit()

                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=bot_message_id,
                    text="Транзакция выполнена успешно!",
                    reply_markup=create_return_keyboard()
                )
        except Exception as e:
            logger.error(f"Ошибка при добавлении транзакции в БД: {e}")
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=bot_message_id,
                text="Произошла ошибка при добавлении транзакции. Пожалуйста, попробуйте еще раз."
            )
        finally:
            await state.set_state(FormTransaction.stop)

# Функция для создания клавиатуры возврата
def create_return_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Вернуться", callback_data="return_to_finance_menu_budget"))
    return keyboard.as_markup()

# Обработчик возврата в меню бюджетов
@view_transactions_router.callback_query(F.data == "return_to_finance_menu_budget")
async def return_to_budgets_handler(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    await budget_menu_finance(callback.message, budget_id, callback.message.message_id)

# Обработчик возврата к списку транзакций
@view_transactions_router.callback_query(F.data == 'back_from_transaction_detail')
async def back_to_transactions_handler(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    category_id = user_data.get('category_id')
    transaction_type = user_data.get('transaction_type')

    if category_id is None or transaction_type is None:
        await callback.answer("Ошибка: идентификатор категории или тип транзакции не найден.", show_alert=True)
        return

    await view_transactions(callback.message, category_id, transaction_type, state)