import logging
from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from start.keyboards import registration_keyboard
from budget.keyboards import budget_menu_keyboard
from start.database import registration

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

registration_router = Router()

async def start_message(message: Message):
    """Отправляет сообщение с предложением пройти регистрацию."""
    logger.info(f"Пользователь {message.from_user.id} начал регистрацию.")
    await message.answer("🔐 Пожалуйста, пройдите регистрацию, чтобы открыть все возможности бота!", reply_markup=registration_keyboard)

@registration_router.callback_query(F.data == 'reg')
async def create_budget(callback: CallbackQuery):
    """Обрабатывает нажатие на кнопку регистрации и переводит пользователя в меню бюджета."""
    logger.info(f"Пользователь {callback.from_user.id} завершил регистрацию.")
    await callback.answer()
    await callback.message.edit_text("💰 Управление бюджетом", reply_markup=budget_menu_keyboard)

@registration_router.message(CommandStart())
async def start(message: Message):
    """Обрабатывает команду /start и проверяет, зарегистрирован ли пользователь."""
    telegram_id = message.from_user.id
    logger.info(f"Пользователь {telegram_id} запустил бота.")
    try:
        result = registration(telegram_id)
        if result == 0:
            await start_message(message)
        else:
            await message.answer("💰 Управление бюджетом", reply_markup=budget_menu_keyboard)
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /start для пользователя {telegram_id}: {e}")
        await message.answer("⚠️ Произошла ошибка. Пожалуйста, попробуйте позже.")