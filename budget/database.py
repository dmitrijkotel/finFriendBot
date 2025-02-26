import sqlite3, aiosqlite
from budget.keyboards import back_complete_keyboard


def add_budget_db(user_id, budget_name, description):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()

    try:
        cursor.execute('INSERT INTO budgets (user_id, budget_name, description) VALUES (?, ?, ?)',
                   (user_id, budget_name, description,))
        db.commit()
        db.close()
        return 'Бюджет успешно создан!'
    except ConnectionError:
        return 'Произошла ошибка, попробуйте снова!'


async def get_budget_details_db(budget_id):
    async with aiosqlite.connect('database.db') as db:
        async with db.execute("SELECT budget_name, description FROM budgets WHERE id = ?", (budget_id,)) as cursor:
            budget = await cursor.fetchone()  # Получаем детали бюджета
    return budget


async def delete_budget_db(budget_id, message):
    async with aiosqlite.connect('database.db') as db:
        try:
            # Проверка существования бюджета с данным budget_id
            async with db.execute("SELECT id FROM budgets WHERE id = ?", (budget_id,)) as cursor:
                budget_exists = await cursor.fetchone()
                if not budget_exists:
                    await message.edit_text("Бюджет не найден!", reply_markup=back_complete_keyboard)
                    return

                    # Удаление бюджета
            async with db.execute("DELETE FROM budgets WHERE id = ?", (budget_id,)) as cursor:
                await db.commit()
                await message.edit_text('Бюджет успешно удалён!',
                                     reply_markup=back_complete_keyboard)  # Сообщение об успешном удалении

        except (sqlite3.Error, aiosqlite.Error) as e:  # Ловим ошибки базы данных
            print(f"Ошибка базы данных: {e}")  # Выводим ошибку в консоль
            await message.edit_text('Произошла ошибка, попробуйте снова!', reply_markup=back_complete_keyboard)


async def get_budgets_from_db(user_id):
    async with aiosqlite.connect('database.db') as conn:
        async with conn.execute("SELECT id, budget_name FROM budgets WHERE user_id = ?", (user_id,)) as cursor:
            buttons = await cursor.fetchall()  # Получаем список с id и name
    return buttons  # Возвращаем полученные данные


from budget.keyboards import back_complete_edit_name_keyboard

async def set_new_budget_name(message, new_name, budget_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE budgets SET budget_name = ? WHERE id = ?", (new_name, budget_id))
    conn.commit()
    conn.close()
    await message.answer('Название бюджета успешно изменено!', reply_markup=back_complete_edit_name_keyboard)

from budget.keyboards import back_complete_edit_description_keyboard

async def set_new_budget_description(message, new_description, budget_id, bot_message_id):
    async with aiosqlite.connect('database.db') as db:
        try:
            async with db.execute("UPDATE budgets SET description = ? WHERE id = ?", (new_description, budget_id)) as cursor:
                await db.commit()  # Формат commit в асинхронном режиме

            # Редактируем сообщение бота
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=bot_message_id,
                text='Описание бюджета успешно изменено!',
                reply_markup=back_complete_edit_description_keyboard
            )
        except (sqlite3.Error, aiosqlite.Error) as e:  # Обработка ошибок базы данных
            print(f"Ошибка базы данных: {e}")  # Логирование ошибки

            # Редактируем сообщение бота в случае ошибки
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=bot_message_id,
                text='Произошла ошибка при обновлении описания бюджета. Попробуйте снова.',
                reply_markup=back_complete_edit_description_keyboard
            )