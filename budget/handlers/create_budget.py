from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from budget.keyboards import budget_menu_keyboard, back_keyboard, add_budget_description_keyboard
from aiogram.fsm.state import State, StatesGroup
from budget.database import add_budget_db

create_budget_router = Router()

class create_budget_states(StatesGroup):
    waiting_for_budget_title = State()
    waiting_for_budget_description = State()

@create_budget_router.callback_query(F.data == 'create_budget_button')
async def create_budget_handler(callback: CallbackQuery, state: FSMContext):
    # Отправляем сообщение с просьбой ввести название бюджета и сохраняем идентификатор
    bot_message = await callback.message.edit_text("📝 Введите название для бюджета:", reply_markup=back_keyboard)
    await state.update_data(bot_message_id=bot_message.message_id)
    await state.set_state(create_budget_states.waiting_for_budget_title)
    await callback.answer()

@create_budget_router.message(create_budget_states.waiting_for_budget_title)
async def create_budget_name(message: Message, state: FSMContext):
    budget_name = message.text
    await state.update_data(budget_name=budget_name)  # Сохраняем название бюджета в состоянии

    # Удаляем сообщение пользователя
    await message.delete()

    # Получаем идентификатор сообщения бота и редактируем его
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
    user_data = await state.get_data()  # Получаем данные состояния
    bot_message_id = user_data.get('bot_message_id')

    if user_data.get('description') == '':
        # Если описание уже пустое (т.е. Нажата кнопка "Skip")
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="📝 Описание бюджета пропущено.",
            reply_markup=budget_menu_keyboard
        )
    else:
        # Обработка введенного описания
        description = message.text
        await state.update_data(description=description)  # Сохраняем описание

        # Удаляем сообщение пользователя
        await message.delete()

        budget_name = user_data.get('budget_name')  # Получаем название бюджета
        telegram_id = message.from_user.id
        result = add_budget_db(telegram_id, budget_name, description)

        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text=result,
            reply_markup=budget_menu_keyboard
        )
    await state.clear()  # Очистка состояния после успешного создания бюджета

@create_budget_router.callback_query(F.data == 'skip_budget_description_button')
async def skip_button(callback: CallbackQuery, state: FSMContext):
    await callback.answer()  # Подтверждаем нажатие кнопки

    # Получаем данные состояния
    user_data = await state.get_data()
    budget_name = user_data.get('budget_name')  # Получаем название бюджета

    # Сохраняем пустое описание в состоянии
    description = ''
    await state.update_data(description=description)

    # Здесь добавляем логику добавления бюджета в базу данных
    telegram_id = callback.from_user.id
    result = add_budget_db(telegram_id, budget_name, description)

    await callback.message.edit_text(result, reply_markup=budget_menu_keyboard)
    await state.clear()  # Очистка состояния после успешного создания бюджета