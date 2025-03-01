import os
import sqlite3
import io
from PIL import Image, ImageDraw, ImageFont

# Определяем путь к шрифту
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'DejaVuSans.ttf')

# Функция для экспорта бюджета в JPEG
def export_budget_to_jpeg(budget_id):
    try:
        with sqlite3.connect('database.db') as db:
            cursor = db.cursor()

            cursor.execute("""
                SELECT budget_name, description, created_at 
                FROM budgets 
                WHERE id = ?
            """, (budget_id,))
            budget = cursor.fetchone()

            if not budget:
                print(f"Бюджет с ID {budget_id} не найден.")
                return None
            
            budget_name, description, created_at = (budget[0] or '', budget[1] or '', budget[2] or '')

            cursor.execute("""
                SELECT c.name, c.type, COALESCE(SUM(t.amount), 0) 
                FROM categories c
                LEFT JOIN transactions t ON c.id = t.category_id
                WHERE c.budget_id = ?
                GROUP BY c.id
            """, (budget_id,))
            categories_summary = cursor.fetchall()

            cursor.execute("""
                SELECT c.name, 
                       t.amount * CASE WHEN c.type = 'expense' THEN -1 ELSE 1 END, 
                       t.date, 
                       t.description, 
                       c.type
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE c.budget_id = ?
                ORDER BY c.type, c.name, t.date
            """, (budget_id,))
            transactions = cursor.fetchall()

            total_income = sum(amount for _, ttype, amount in categories_summary if ttype == 'income')
            total_expense = sum(amount for _, ttype, amount in categories_summary if ttype == 'expense')
            balance = total_income - total_expense

        # Создаем изображение
        img_width, img_height = 1500, 3000
        img = Image.new('RGB', (img_width, img_height), "white")
        draw = ImageDraw.Draw(img)

        # Подключаем шрифт
        try:
            font = ImageFont.truetype(FONT_PATH, 30)
            font_small = ImageFont.truetype(FONT_PATH, 24)
        except IOError:
            print("Ошибка загрузки шрифта, используем стандартный.")
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Отрисовка заголовка
        y_position = 50
        draw.text((50, y_position), f"Название бюджета: {budget_name}", fill="black", font=font)
        y_position += 50
        draw.text((50, y_position), f"Описание: {description}", fill="black", font=font_small)
        y_position += 40
        draw.text((50, y_position), f"Дата создания: {created_at}", fill="black", font=font_small)
        y_position += 60

        # Отрисовка таблицы
        def draw_table(title, data, start_y, color):
            draw.rectangle([50, start_y, img_width - 50, start_y + 40], fill=color)
            draw.text((60, start_y + 5), title, fill="black", font=font)
            y = start_y + 50

            for row in data:
                draw.text((60, y), f"{row[0]}", fill="black", font=font_small)
                draw.text((550, y), f"{row[1]}", fill="black", font=font_small)
                draw.text((750, y), f"{row[2]}", fill="black", font=font_small)
                draw.text((1100, y), f"{row[3]}", fill="black", font=font_small)
                y += 40

            return y + 20

        income_data = [["Категория", "Сумма", "Дата", "Описание"]]
        expense_data = [["Категория", "Сумма", "Дата", "Описание"]]

        for category, category_type, category_total in categories_summary:
            category = category or ''
            if category_type == 'income':
                income_data.append([f"{category} (Всего: {category_total})", "", "", ""])
            else:
                expense_data.append([f"{category} (Всего: {category_total})", "", "", ""])

            for c_name, amount, date, desc, ttype in transactions:
                if c_name == category and ttype == category_type:
                    row = ["", f"{amount:.2f}", date, desc]
                    (income_data if category_type == 'income' else expense_data).append(row)

        y_position = draw_table("ДОХОДЫ", income_data, y_position, "lightblue")
        y_position = draw_table("РАСХОДЫ", expense_data, y_position, "pink")

        # Итоговая информация
        draw.text((50, y_position), "ИТОГ:", fill="black", font=font)
        draw.text((100, y_position + 40), f"Общий доход: {total_income:.2f}", fill="green", font=font_small)
        draw.text((100, y_position + 80), f"Общий расход: {total_expense:.2f}", fill="red", font=font_small)
        draw.text((100, y_position + 120), f"Баланс: {balance:.2f}", fill="blue", font=font_small)

        # Сохранение в буфер
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=95)
        output.seek(0)

        return output

    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return None
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None
