import os
import sqlite3
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# Определяем путь к шрифту
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'DejaVuSans.ttf')

# Регистрируем шрифт
pdfmetrics.registerFont(TTFont('DejaVu', FONT_PATH))

# Функция для экспорта бюджета в PDF
def export_budget_to_pdf(budget_id):
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
            
            budget_name, description, created_at = map(lambda x: x if x else '', budget)

            cursor.execute("""
                SELECT c.name, c.type, COALESCE(SUM(t.amount), 0) 
                FROM categories c
                LEFT JOIN transactions t ON c.id = t.category_id
                WHERE c.budget_id = ?
                GROUP BY c.id
            """, (budget_id,))
            categories_summary = cursor.fetchall()

            cursor.execute("""
                SELECT c.name AS category_name, 
                       t.amount * CASE WHEN c.type = 'expense' THEN -1 ELSE 1 END AS amount, 
                       t.date, 
                       t.description, 
                       c.type
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE c.budget_id = ?
                ORDER BY c.type, c.name, t.date
            """, (budget_id,))
            transactions = cursor.fetchall()

            # Декодируем строки и заменяем ошибочные символы
            def safe_decode(value):
                if isinstance(value, bytes):
                    return value.decode('utf-8', 'replace')  # заменяем битые символы
                return str(value)

            budget_name = safe_decode(budget_name)
            description = safe_decode(description)
            transactions = [(safe_decode(c), a, safe_decode(d), safe_decode(desc), safe_decode(t)) for c, a, d, desc, t in transactions]

            total_income = sum(amount for _, ttype, amount in categories_summary if ttype == 'income')
            total_expense = sum(amount for _, ttype, amount in categories_summary if ttype == 'expense')
            balance = total_income - total_expense

        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Russian', fontName='DejaVu', fontSize=12))

        elements.append(Paragraph(f"<b>Название бюджета:</b> {budget_name}", styles['Russian']))
        elements.append(Paragraph(f"<b>Описание:</b> {description}", styles['Russian']))
        elements.append(Paragraph(f"<b>Дата создания:</b> {created_at}", styles['Russian']))
        elements.append(Spacer(1, 12))

        # Таблицы
        income_data = [["Категория", "Сумма", "Дата", "Описание"]]
        expense_data = [["Категория", "Сумма", "Дата", "Описание"]]

        for category, category_type, category_total in categories_summary:
            category = safe_decode(category)
            if category_type == 'income':
                income_data.append([f"{category} (Всего: {category_total})", "", "", ""])
            else:
                expense_data.append([f"{category} (Всего: {category_total})", "", "", ""])

            for c_name, amount, date, desc, ttype in transactions:
                if c_name == category and ttype == category_type:
                    row = ["", f"{amount:.2f}", date, desc]
                    (income_data if category_type == 'income' else expense_data).append(row)

        # Создание таблиц
        def create_table(data, color):
            table = Table(data, colWidths=[200, 100, 130, 150])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), color),
                ('TEXTCOLOR', (1, 1), (-1, -1), colors.black),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 0), (-1, -1), 'DejaVu')
            ]))
            return table
        elements.append(Spacer(1, 50))  # Увеличенный отступ перед словом "ДОХОДЫ"
        elements.append(Paragraph("<b>ДОХОДЫ</b>", styles['Russian']))
        elements.append(Spacer(1, 13))  # Увеличенный отступ перед таблицей доходов
        elements.append(create_table(income_data, colors.lightblue))
        elements.append(Spacer(1, 30))  # Увеличенный отступ перед разделом расходов

        elements.append(Paragraph("<b>РАСХОДЫ</b>", styles['Russian']))
        elements.append(Spacer(1, 13))  # Увеличенный отступ перед таблицей расходов
        elements.append(create_table(expense_data, colors.pink))
        elements.append(Spacer(1, 30))  # Увеличенный отступ перед итогами

        # Итог
        elements.append(Paragraph("<b>ИТОГ</b>", styles['Russian']))
        total_data = [["Общий доход:", f"{total_income:.2f}"], ["Общий расход:", f"{total_expense:.2f}"], ["Баланс:", f"{balance:.2f}"]]
        total_table = Table(total_data, colWidths=[200, 100])
        total_table.setStyle(TableStyle([
            ('TEXTCOLOR', (1, 0), (1, 0), colors.green),
            ('TEXTCOLOR', (1, 1), (1, 1), colors.red),
            ('TEXTCOLOR', (1, 2), (1, 2), colors.blue),
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVu')
        ]))
        elements.append(total_table)

        doc.build(elements)
        output.seek(0)
        return output

    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return None
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None
