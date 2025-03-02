from aiogram import Router, F
from aiogram.types import CallbackQuery
from budget.keyboards import budget_menu_keyboard

menu_budget_router = Router()

@menu_budget_router.callback_query(F.data == 'cancel_button')
async def cancel_budget(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Вы вернулись Выберите действие:", reply_markup=budget_menu_keyboard)

@menu_budget_router.callback_query(F.data == 'back_button')
async def back_to_menu(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("🔙 Вы вернулись в главное меню. Выберите действие:", reply_markup=budget_menu_keyboard)
