from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, BufferedInputFile
from aiogram.fsm.state import State, StatesGroup
from budget.handlers.view_budget import budget_menu_finance
from budget.report.generation.excel import export_budget_to_excel
from budget.report.generation.jpeg import export_budget_to_jpeg
from budget.report.generation.pdf import export_budget_to_pdf
from budget.report.keyboards import report_format_keyboard, back_menu_keyboard

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
        return

    await callback.message.edit_text("📊 Выберите формат файла для отчёта:", reply_markup=report_format_keyboard)
    await callback.answer()

async def send_report(callback: CallbackQuery, file_stream, filename, caption, state: FSMContext):
    if file_stream is None:
        await callback.message.answer("Ошибка: не удалось создать отчёт. Проверьте данные и попробуйте снова.")
        return
    
    # Удаляем меню перед отправкой отчёта
    await callback.message.delete()

    file = BufferedInputFile(file_stream.read(), filename=filename)
    sent_message = await callback.message.answer_document(file, caption=caption, reply_markup=back_menu_keyboard)
    
    # Сохраняем ID отправленного сообщения с отчётом
    await state.update_data(report_message_id=sent_message.message_id)

@report_router.callback_query(F.data == 'excel_report_format_button')
async def generate_excel_report(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    if not budget_id:
        await callback.message.answer("Ошибка: ID бюджета не найден. Попробуйте снова.")
        return

    file_stream = export_budget_to_excel(budget_id)
    await send_report(callback, file_stream, f"ОТЧЁТ budget_{budget_id}.xlsx", "📑 Ваш EXCEL-отчёт по бюджету.", state)

@report_router.callback_query(F.data == 'pdf_report_format_button')
async def generate_pdf_report(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    if not budget_id:
        await callback.message.answer("Ошибка: ID бюджета не найден. Попробуйте снова.")
        return

    file_stream = export_budget_to_pdf(budget_id)
    await send_report(callback, file_stream, f"ОТЧЁТ budget_{budget_id}.pdf", "📄 Ваш PDF-отчёт по бюджету.", state)

@report_router.callback_query(F.data == 'jpeg_report_format_button')
async def generate_jpeg_report(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    if not budget_id:
        await callback.message.answer("Ошибка: ID бюджета не найден. Попробуйте снова.")
        return

    file_stream = export_budget_to_jpeg(budget_id)
    await send_report(callback, file_stream, f"ОТЧЁТ budget_{budget_id}.jpg", "🖼 Ваш JPEG-отчёт по бюджету.", state)

@report_router.callback_query(F.data == 'back_menu_button')
async def back_to_budget(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')
    
    # Удаляем сообщение с отчётом, если оно существует
    report_message_id = user_data.get('report_message_id')
    if report_message_id:
        try:
            await callback.bot.delete_message(callback.message.chat.id, report_message_id)
        except Exception:
            pass  # Игнорируем ошибки, если сообщение уже удалено

    await report_menu_fun(callback, state)


async def report_menu_fun(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    if not budget_id:
        await callback.message.answer("Ошибка: бюджет не найден.")
        return

    await callback.message.answer("📊 Выберите формат файла для отчёта:", reply_markup=report_format_keyboard)
    await callback.answer()

@report_router.callback_query(F.data == 'back_report_button')
async def back_to_budget(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    await budget_menu_finance(callback.message, budget_id, callback.message.message_id)