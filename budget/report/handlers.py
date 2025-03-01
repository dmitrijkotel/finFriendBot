from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, BufferedInputFile
from aiogram.fsm.state import State, StatesGroup
from budget.handlers.view_budget import budget_menu_finance
from budget.report.generation.excel import export_budget_to_excel
from budget.report.generation.jpeg import export_budget_to_jpeg
from budget.report.generation.pdf import export_budget_to_pdf
from budget.report.keyboards import report_format_keyboard


report_router = Router()

class DateReportBudget(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_end_date = State()
    stop = State()

@report_router.callback_query(F.data == 'back_report_button')
async def back_to_budget(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')
    await budget_menu_finance(callback.message, budget_id, callback.message.message_id)


@report_router.callback_query(F.data == 'report_budget_button')
async def full_date_range_report(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    if not budget_id:
        await callback.message.answer("Ошибка: бюджет не найден.")
        return

    # Обновляем сообщение
    await callback.message.edit_text("Выберите формат файла для отчёта:", reply_markup=report_format_keyboard)

    await callback.answer()

@report_router.callback_query(F.data == 'excel_report_format_button')
async def generate_excel_report(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    if budget_id is None:
        await callback.message.answer("Ошибка: ID бюджета не найден. Попробуйте снова.")
        return

    file_stream = export_budget_to_excel(budget_id)

    if file_stream is None:
        await callback.message.answer("Ошибка: не удалось создать отчёт. Проверьте данные и попробуйте снова.")
        return

    file = BufferedInputFile(file_stream.read(), filename=f"ОТЧЁТ budget_{budget_id}.xlsx")
    await callback.message.answer_document(file)

@report_router.callback_query(F.data == 'pdf_report_format_button')
async def generate_pdf_report(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    if budget_id is None:
        await callback.message.answer("Ошибка: ID бюджета не найден. Попробуйте снова.")
        return

    file_stream = export_budget_to_pdf(budget_id)

    if file_stream is None:
        await callback.message.answer("Ошибка: не удалось создать отчёт. Проверьте данные и попробуйте снова.")
        return

    file = BufferedInputFile(file_stream.read(), filename=f"ОТЧЁТ budget_{budget_id}.pdf")
    await callback.message.answer_document(file, caption="📄 Ваш PDF-отчёт по бюджету.")

@report_router.callback_query(F.data == 'jpeg_report_format_button')
async def generate_jpeg_report(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    budget_id = user_data.get('budget_id')

    if budget_id is None:
        await callback.message.answer("Ошибка: ID бюджета не найден. Попробуйте снова.")
        return

    file_stream = export_budget_to_jpeg(budget_id)  # Генерируем отчет в JPEG

    if file_stream is None:
        await callback.message.answer("Ошибка: не удалось создать отчёт. Проверьте данные и попробуйте снова.")
        return

    # ✅ Создаем файл и отправляем пользователю
    file = BufferedInputFile(file_stream.getvalue(), filename=f"ОТЧЁТ budget_{budget_id}.jpg")
    await callback.message.answer_document(file, caption="🖼 Ваш JPEG-отчёт по бюджету.")

