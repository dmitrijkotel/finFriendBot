import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, BufferedInputFile
from aiogram.fsm.state import State, StatesGroup
from budget.handlers.view_budget import budget_menu_finance
from budget.report.generation.excel import export_budget_to_excel
from budget.report.generation.jpeg import export_budget_to_jpeg
from budget.report.generation.pdf import export_budget_to_pdf
from budget.report.keyboards import report_format_keyboard, back_menu_keyboard

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

report_router = Router()

class DateReportBudget(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_end_date = State()
    stop = State()

@report_router.callback_query(F.data == 'report_budget_button')
async def report_menu(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    if not budget_id:
        await callback.message.answer("Ошибка: бюджет не найден.")
        logger.warning("Пользователь %s попытался создать отчёт без ID бюджета", callback.from_user.id)
        return

    logger.info("Пользователь %s открывает меню отчётов для бюджета %s", callback.from_user.id, budget_id)
    await callback.message.edit_text("📊 Выберите формат файла для отчёта:", reply_markup=report_format_keyboard)
    await callback.answer()

async def send_report(callback: CallbackQuery, file_stream, filename, caption, state: FSMContext):
    if file_stream is None:
        await callback.message.answer("Ошибка: не удалось создать отчёт. Проверьте данные и попробуйте снова.")
        logger.error("Ошибка при создании отчёта для пользователя %s", callback.from_user.id)
        return
    
    await callback.message.delete()
    file = BufferedInputFile(file_stream.read(), filename=filename)
    sent_message = await callback.message.answer_document(file, caption=caption, reply_markup=back_menu_keyboard)
    await state.update_data(report_message_id=sent_message.message_id)
    logger.info("Пользователь %s получил отчёт: %s", callback.from_user.id, filename)

@report_router.callback_query(F.data == 'excel_report_format_button')
async def generate_excel_report(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    if not budget_id:
        await callback.message.answer("Ошибка: ID бюджета не найден. Попробуйте снова.")
        logger.warning("Пользователь %s пытался создать EXCEL-отчёт без ID бюджета", callback.from_user.id)
        return

    logger.info("Пользователь %s запрашивает EXCEL-отчёт для бюджета %s", callback.from_user.id, budget_id)
    file_stream = export_budget_to_excel(budget_id)
    await send_report(callback, file_stream, f"ОТЧЁТ budget_{budget_id}.xlsx", "📑 Ваш EXCEL-отчёт по бюджету.", state)

@report_router.callback_query(F.data == 'pdf_report_format_button')
async def generate_pdf_report(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    if not budget_id:
        await callback.message.answer("Ошибка: ID бюджета не найден. Попробуйте снова.")
        logger.warning("Пользователь %s пытался создать PDF-отчёт без ID бюджета", callback.from_user.id)
        return

    logger.info("Пользователь %s запрашивает PDF-отчёт для бюджета %s", callback.from_user.id, budget_id)
    file_stream = export_budget_to_pdf(budget_id)
    await send_report(callback, file_stream, f"ОТЧЁТ budget_{budget_id}.pdf", "📄 Ваш PDF-отчёт по бюджету.", state)

@report_router.callback_query(F.data == 'jpeg_report_format_button')
async def generate_jpeg_report(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    if not budget_id:
        await callback.message.answer("Ошибка: ID бюджета не найден. Попробуйте снова.")
        logger.warning("Пользователь %s пытался создать JPEG-отчёт без ID бюджета", callback.from_user.id)
        return

    logger.info("Пользователь %s запрашивает JPEG-отчёт для бюджета %s", callback.from_user.id, budget_id)
    file_stream = export_budget_to_jpeg(budget_id)
    await send_report(callback, file_stream, f"ОТЧЁТ budget_{budget_id}.jpg", "🖼 Ваш JPEG-отчёт по бюджету.", state)

@report_router.callback_query(F.data == 'back_menu_button')
async def back_to_budget(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')
    
    report_message_id = user_data.get('report_message_id')
    if report_message_id:
        try:
            await callback.bot.delete_message(callback.message.chat.id, report_message_id)
            logger.info("Удалено сообщение с отчётом для пользователя %s", callback.from_user.id)
        except Exception as e:
            logger.error("Ошибка при удалении сообщения с отчётом: %s", str(e))

    await report_menu_fun(callback, state)

async def report_menu_fun(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    if not budget_id:
        await callback.message.answer("Ошибка: бюджет не найден.")
        logger.warning("Пользователь %s пытался открыть меню отчётов без ID бюджета", callback.from_user.id)
        return

    await callback.message.answer("📊 Выберите формат файла для отчёта:", reply_markup=report_format_keyboard)
    await callback.answer()
    logger.info("Пользователь %s вернулся в меню отчётов", callback.from_user.id)

@report_router.callback_query(F.data == 'back_report_button')
async def back_to_budget(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    logger.info("Пользователь %s вернулся в главное меню бюджета %s", callback.from_user.id, budget_id)
    await budget_menu_finance(callback.message, budget_id, callback.message.message_id)