import sqlite3

def get_budget_created_at(budget_id: int) -> str | None:
    """Получает дату создания бюджета по его ID из SQLite."""
    conn = sqlite3.connect("database.db")  # Подключение к БД (замени на свой путь)
    cursor = conn.cursor()
    
    cursor.execute("SELECT created_at FROM budgets WHERE id = ?", (budget_id,))
    row = cursor.fetchone()
    
    conn.close()  # Закрываем соединение

    if row:
        return row[0]  # Возвращаем дату в формате 'YYYY-MM-DD'
    return None
