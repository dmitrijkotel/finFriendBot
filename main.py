import asyncio
import logging
from aiogram import Bot, Dispatcher
import os
from dotenv import load_dotenv

from create_tables_db import create_tables_db
from start.handlers.menu import menu_budget_router
from start.handlers.registration import registration_router
from budget.handlers.create_budget import create_budget_router
from budget.handlers.view_budget import view_budget_router
from budget.finance.expense.add_expenses_categories import create_expenses_category_router
from budget.finance.expense.view_expenses_category import view_expenses_category_router
from budget.finance.income.add_income_categories import create_income_category_router
from budget.finance.income.view_income_categories import view_income_category_router
from budget.finance.view_transactions import view_transactions_router

load_dotenv()
TOKEN = os.getenv('TOKEN')


bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    dp.include_router(registration_router)
    dp.include_router(menu_budget_router)
    dp.include_router(create_budget_router)
    dp.include_router(view_budget_router)
    dp.include_router(create_expenses_category_router)
    dp.include_router(view_expenses_category_router)
    dp.include_router(create_income_category_router)
    dp.include_router(view_income_category_router)
    dp.include_router(view_transactions_router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    create_tables_db()
    logging.basicConfig(level=logging.INFO)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot stopped by user.')