import sqlite3

def create_tables_db():
    # Подключаемся к базе данных (или создаем ее, если она не существует)
    db = sqlite3.connect('database.db')
    cursor = db.cursor()

    # Создание таблицы пользователей
    cursor.execute('''  
    CREATE TABLE IF NOT EXISTS users (  
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        telegram_id INTEGER UNIQUE NOT NULL  
    )''')

    # Создание таблицы бюджетов
    cursor.execute("""  
    CREATE TABLE IF NOT EXISTS budgets (  
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        user_id INTEGER NOT NULL,  
        budget_name TEXT NOT NULL,  
        description TEXT,  
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE  
    );  
    """)

    # Создание таблицы категорий
    cursor.execute("""  
    CREATE TABLE IF NOT EXISTS categories (  
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        budget_id INTEGER NOT NULL,  
        name TEXT NOT NULL,  
        description TEXT,
        type TEXT NOT NULL CHECK (type IN ('income', 'expense')),  
        FOREIGN KEY (budget_id) REFERENCES budgets(id) ON DELETE CASCADE  
    );  
    """)

    # Создание таблицы транзакций (объединенная для доходов и расходов)
    cursor.execute("""  
    CREATE TABLE IF NOT EXISTS transactions (  
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        category_id INTEGER NOT NULL,  
        amount REAL NOT NULL CHECK (amount >= 0),  
        type TEXT NOT NULL CHECK (type IN ('income', 'expense')),  
        date TEXT NOT NULL,  
        description TEXT,  
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE  
    );  
    """)

    # Создание индексов для ускорения запросов
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_categories_budget_id ON categories(budget_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_user_id ON budgets(user_id);")

    # Сохраняем изменения и закрываем соединение
    db.commit()
    db.close()

# Вызов функции для создания таблиц
create_tables_db()