from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.states import OrderState
from bot.database.queries import create_order
from bot.keyboards.inline import contact_keyboard, order_confirm_keyboard, back_to_menu_keyboard

router = Router()


@router.message(F.text == "💬 Заказать")
async def contact_menu(message: Message):
    await message.answer(
        "<b>💬 Как связаться?</b>\n\n"
        "Выберите удобный способ:",
        reply_markup=contact_keyboard(),
    )


@router.callback_query(F.data == "order_start")
async def start_order(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "<b>📝 Заявка на заказ</b>\n\n"
        "Опишите вашу задачу или идею:",
        reply_markup=None,
    )
    await callback.answer()
    await state.set_state(OrderState.description)


@router.message(OrderState.description)
async def order_description(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 5:
        await message.answer("Описание слишком короткое. Подробнее опишите задачу:")
        return
    await state.update_data(description=message.text)
    await message.answer(
        "Какой примерный бюджет? (или «договорная»)"
    )
    await state.set_state(OrderState.budget)


@router.message(OrderState.budget)
async def order_budget(message: Message, state: FSMContext):
    await state.update_data(budget=message.text)
    await message.answer(
        "Укажите ваш контакт (username в Telegram или другой способ связи):"
    )
    await state.set_state(OrderState.contact)


@router.message(OrderState.contact)
async def order_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()
    preview = (
        f"<b>📋 Ваша заявка:</b>\n\n"
        f"<b>Задача:</b> <i>{data['description']}</i>\n"
        f"<b>Бюджет:</b> {data['budget']}\n"
        f"<b>Контакт:</b> {data['contact']}\n\n"
        "Отправить заявку?"
    )
    await message.answer(preview, reply_markup=order_confirm_keyboard())
    await state.set_state(OrderState.confirm)


@router.callback_query(F.data == "order_confirm", OrderState.confirm)
async def confirm_order(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    order = await create_order(
        session, callback.from_user.id,
        data["description"], data["budget"], data["contact"],
    )
    await callback.message.edit_text(
        "<b>✅ Заявка отправленa!</b>\n\n"
        "Я свяжусь с вами в ближайшее время.",
        reply_markup=back_to_menu_keyboard(),
    )
    await callback.answer()
    await state.clear()

    admin_text = (
        f"<b>📩 Новая заявка #{order.id}</b>\n\n"
        f"От: {callback.from_user.full_name} (@{callback.from_user.username or 'нет'})\n"
        f"<b>Задача:</b> {data['description']}\n"
        f"<b>Бюджет:</b> {data['budget']}\n"
        f"<b>Контакт:</b> {data['contact']}"
    )
    from bot.config import ADMIN_ID
    try:
        await callback.bot.send_message(ADMIN_ID, admin_text)
    except Exception:
        pass


@router.callback_query(F.data == "order_cancel")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Заявка отменена.", reply_markup=back_to_menu_keyboard())
    await callback.answer()
