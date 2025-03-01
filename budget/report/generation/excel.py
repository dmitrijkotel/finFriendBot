import sqlite3
import pandas as pd
import io

def export_budget_to_excel(budget_id):
    try:
        with sqlite3.connect('database.db') as db:
            cursor = db.cursor()

            # Получение информации о бюджете
            cursor.execute("""
                SELECT budget_name, description, created_at 
                FROM budgets 
                WHERE id = ?
            """, (budget_id,))
            budget = cursor.fetchone()

            if not budget:
                print(f"Бюджет с ID {budget_id} не найден.")
                return None
            
            budget_name, description, created_at = budget

            # Получение всех категорий с их суммарными доходами/расходами
            cursor.execute("""
                SELECT c.name, c.type, COALESCE(SUM(t.amount), 0) 
                FROM categories c
                LEFT JOIN transactions t ON c.id = t.category_id
                WHERE c.budget_id = ?
                GROUP BY c.id
            """, (budget_id,))
            categories_summary = cursor.fetchall()

            # Получение всех транзакций
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

            # Подсчет общего дохода и расхода
            total_income = sum(amount for _, ttype, amount in categories_summary if ttype == 'income')
            total_expense = sum(amount for _, ttype, amount in categories_summary if ttype == 'expense')  # Убрали лишний минус
            balance = total_income - total_expense

        # Формирование таблицы с отчетом
        data = [
            ["Название бюджета:", budget_name],
            ["Описание:", description],
            ["Дата создания:", created_at],
            ["", ""],  # Разделительная строка
        ]

        income_start = len(data)
        data.append(["💰 ДОХОДЫ", "", "", ""])  

        for category, category_type, category_total in categories_summary:
            if category_type == 'income':
                data.append([f"{category} (Всего: {category_total})", "", "", ""])
                data.append(["Сумма", "Дата", "Описание"])
                for c_name, amount, date, desc, ttype in transactions:
                    if c_name == category and ttype == 'income':
                        data.append([amount, date, desc])
                data.append(["", ""])  # Разделитель

        expense_start = len(data)
        data.append(["💸 РАСХОДЫ", "", "", ""])  

        for category, category_type, category_total in categories_summary:
            if category_type == 'expense':
                data.append([f"{category} (Всего: {category_total})", "", "", ""])  # Убрали лишний минус
                data.append(["Сумма", "Дата", "Описание"])
                for c_name, amount, date, desc, ttype in transactions:
                    if c_name == category and ttype == 'expense':
                        data.append([amount, date, desc])
                data.append(["", ""])  # Разделитель

        total_start = len(data)
        data.append(["📊 ИТОГ", "Сумма"])
        data.append(["Общий доход:", total_income])
        data.append(["Общий расход:", total_expense])  # Исправлено
        data.append(["Баланс:", balance])

        df_report = pd.DataFrame(data)

        # Создание файла в памяти
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_report.to_excel(writer, sheet_name='Бюджетный отчет', index=False, header=False)

            # Форматирование
            workbook = writer.book
            worksheet = writer.sheets['Бюджетный отчет']

            # Форматы
            bold_format = workbook.add_format({'bold': True, 'font_size': 12})
            header_format = workbook.add_format({'bold': True, 'bg_color': '#DCE6F1', 'border': 1})
            category_format = workbook.add_format({'bold': True, 'font_size': 11, 'bg_color': '#F4B084', 'border': 1})
            money_format = workbook.add_format({'num_format': '#,##0.00', 'font_color': 'green', 'border': 1})
            money_negative_format = workbook.add_format({'num_format': '#,##0.00', 'font_color': 'red', 'border': 1})  # Исправлено
            total_expense_format = workbook.add_format({'bold': True, 'font_color': 'red', 'font_size': 12})  # Новый формат
            date_format = workbook.add_format({'num_format': 'dd.mm.yyyy', 'border': 1})
            border_format = workbook.add_format({'border': 1})
            black_text_format = workbook.add_format({'font_color': 'black', 'bold': True})  # Черный цвет

            # Ширина колонок
            worksheet.set_column('A:A', 30)  # Категории / описание
            worksheet.set_column('B:B', 15, money_format)  # Сумма
            worksheet.set_column('C:C', 35, date_format)  # Дата
            worksheet.set_column('D:D', 40)  # Описание

            # Делаем данные о бюджете черными
            worksheet.write('A1', "Название бюджета:", black_text_format)
            worksheet.write('B1', budget_name, black_text_format)

            worksheet.write('A2', "Описание:", black_text_format)
            worksheet.write('B2', description, black_text_format)

            worksheet.write('A3', "Дата создания:", black_text_format)
            worksheet.write('B3', created_at, black_text_format)

            # Стилизация заголовков
            worksheet.write(f'A{income_start + 1}', '💰 ДОХОДЫ', bold_format)
            worksheet.write(f'A{expense_start + 1}', '💸 РАСХОДЫ', bold_format)
            worksheet.write(f'A{total_start + 1}', '📊 ИТОГ', bold_format)

            # Выделяем общий расход красным
            worksheet.write(f'B{total_start + 3}', total_expense, total_expense_format)

            # Разделение категорий с рамками
            row = income_start + 2
            for category, category_type, category_total in categories_summary:
                if category_type == 'income':
                    worksheet.write(f'A{row}', f"{category} (Всего: {category_total})", category_format)
                    row += 1
                    worksheet.write(f'A{row}', "Сумма", header_format)
                    worksheet.write(f'B{row}', "Дата", header_format)
                    worksheet.write(f'C{row}', "Описание", header_format)
                    row += 1
                    for c_name, amount, date, desc, ttype in transactions:
                        if c_name == category and ttype == 'income':
                            worksheet.write(f'A{row}', amount, money_format)
                            worksheet.write(f'B{row}', date, date_format)
                            worksheet.write(f'C{row}', desc, border_format)
                            row += 1
                    row += 1  # Разделительная строка

            row = expense_start + 2
            for category, category_type, category_total in categories_summary:
                if category_type == 'expense':
                    worksheet.write(f'A{row}', f"{category} (Всего: {category_total})", category_format)
                    row += 1
                    worksheet.write(f'A{row}', "Сумма", header_format)
                    worksheet.write(f'B{row}', "Дата", header_format)
                    worksheet.write(f'C{row}', "Описание", header_format)
                    row += 1
                    for c_name, amount, date, desc, ttype in transactions:
                        if c_name == category and ttype == 'expense':
                            worksheet.write(f'A{row}', amount, money_negative_format)
                            worksheet.write(f'B{row}', date, date_format)
                            worksheet.write(f'C{row}', desc, border_format)
                            row += 1
                    row += 1  # Разделительная строка

        output.seek(0)
        return output

    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return None
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None
