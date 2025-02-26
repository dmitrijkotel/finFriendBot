import sqlite3

def registration(telegram_id):
    # Функция проверки на наличие пользователя в базе данных
    def user_exists():
        db = sqlite3.connect('database.db')
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        exists = cursor.fetchone() is not None
        db.close()
        return exists

    # Функция создания пользователя
    def create_user():
        db = sqlite3.connect('database.db')
        cursor = db.cursor()
        cursor.execute('INSERT INTO users (telegram_id) VALUES (?)', (telegram_id,))
        db.commit()
        db.close()
        return 0

    if user_exists():
        return 1
    else:
        return create_user()