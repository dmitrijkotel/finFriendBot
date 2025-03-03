import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from budget.keyboards import budget_menu_keyboard

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

menu_budget_router = Router()

@menu_budget_router.callback_query(F.data == 'cancel_button')
async def cancel_budget(callback: CallbackQuery):
    logger.info("Обработан callback: cancel_button от пользователя %s", callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text("Вы вернулись Выберите действие:", reply_markup=budget_menu_keyboard)

@menu_budget_router.callback_query(F.data == 'back_button')
async def back_to_menu(callback: CallbackQuery):
    logger.info("Обработан callback: back_button от пользователя %s", callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text("🔙 Вы вернулись в главное меню. Выберите действие:", reply_markup=budget_menu_keyboard)
