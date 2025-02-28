import sqlite3
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from budget.finance.keyboards import back_income_categories_keyboard as kb_back
from budget.finance.keyboards import skip_description_income_keyboard as skip_keyboard
from budget.handlers.view_budget import budget_menu_finance

create_income_category_router = Router()


class CreateIncomeCategoryStates(StatesGroup):
    waiting_for_category_title = State()
    waiting_for_category_description = State()
    stop = State()


budget_id_g = 0


def add_income_category_db(budget_id, category_name, description):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        cursor.execute("""  
            INSERT INTO categories (budget_id, name, type, description)   
            VALUES (?, ?, 'income', ?)""",
                       (budget_id, category_name, description))
        conn.commit()
        return "Категория дохода успешно добавлена!"
    except Exception as e:
        conn.rollback()
        return f"Произошла ошибка: {str(e)}"
    finally:
        cursor.close()
        conn.close()


@create_income_category_router.callback_query(F.data == 'add_income_category_button')
async def create_income_category_handler(callback: CallbackQuery, state: FSMContext):

    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')
    print(f"Создание категории: budget_id = {budget_id}")  # Отладка

    if not budget_id:
        await callback.answer("Ошибка: идентификатор бюджета не найден.")
        return

    bot_message = await callback.message.edit_text("Введите название для категории дохода:", reply_markup=kb_back)
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

    print(f"Название категории: {category_name}")  # Отладка

    await message.delete()  # Удаляем сообщение пользователя

    user_data = await state.get_data()
    bot_message_id = user_data.get('bot_message_id')

    # Редактируем сообщение бота
    if bot_message_id is not None:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="Введите описание категории (или нажмите 'Пропустить'):",
            reply_markup=skip_keyboard
        )
    else:
        # Если идентификатор сообщения бота не найден, отправляем новое сообщение
        bot_message = await message.answer(
            "Введите описание категории (или нажмите 'Пропустить'):",
            reply_markup=skip_keyboard
        )
        await state.update_data(bot_message_id=bot_message.message_id)

    await state.set_state(CreateIncomeCategoryStates.waiting_for_category_description)


@create_income_category_router.callback_query(F.data == "skip_income_categories_button")
async def skip_description_handler(callback: CallbackQuery, state: FSMContext):
    print("Пропуск описания категории")  # Отладка
    user_data = await state.get_data()
    category_name = user_data.get('category_name')
    budget_id = user_data.get('budget_id')
    bot_message_id = user_data.get('bot_message_id')

    description = None

    # Добавляем категорию в БД
    add_income_category_db(budget_id, category_name, description)

    await state.set_state(CreateIncomeCategoryStates.stop)

    if bot_message_id:
        # Передаём callback.message вместо callback
        await budget_menu_finance(callback.message, budget_id, bot_message_id)
    else:
        # Если ID сообщения нет, отправляем новое меню и запоминаем его
        sent_message = await budget_menu_finance(callback.message, budget_id)
        await state.update_data(bot_message_id=sent_message.message_id)

    # Закрываем всплывающее уведомление
    await callback.answer()




@create_income_category_router.message(CreateIncomeCategoryStates.waiting_for_category_description)
async def create_income_category_description(message: Message, state: FSMContext):
    print("Получение описания категории")  # Отладка
    await message.delete()  # Удаляем сообщение пользователя

    user_data = await state.get_data()
    category_name = user_data.get('category_name')
    budget_id = user_data.get('budget_id')

    description = message.text
    print(f"Описание категории: {description}")  # Отладка

    # Добавляем категорию в БД
    add_income_category_db(budget_id, category_name, description)

    await state.set_state(CreateIncomeCategoryStates.stop)

    # Получаем ID старого сообщения бота
    bot_message_id = user_data.get('bot_message_id')

    if bot_message_id:
        # Если ID есть — обновляем сообщение
        await budget_menu_finance(message, budget_id, bot_message_id)
    else:
        # Если ID нет — просто отправляем меню и запоминаем его
        sent_message = await budget_menu_finance(message, budget_id)
        await state.update_data(bot_message_id=sent_message.message_id)
