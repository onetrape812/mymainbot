from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import ADMIN_ID
from bot.database.queries import (
    get_pending_reviews,
    approve_review,
    reject_review,
    delete_review,
    get_all_reviews,
    get_user_count,
    get_review_count,
    get_order_count,
)
from bot.keyboards.inline import moderation_keyboard

router = Router()


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    from bot.keyboards.inline import admin_menu
    await message.answer(
        "<b>🛠 Админ-панель</b>\n\nВыберите действие:",
        reply_markup=admin_menu(),
    )


@router.message(F.text == "📊 Статистика")
async def stats(message: Message, session: AsyncSession):
    if message.from_user.id != ADMIN_ID:
        return
    users = await get_user_count(session)
    reviews = await get_review_count(session)
    orders = await get_order_count(session)
    await message.answer(
        f"<b>📊 Статистика бота</b>\n\n"
        f"👥 Пользователей: <b>{users}</b>\n"
        f"⭐️ Отзывов: <b>{reviews}</b>\n"
        f"📩 Заявок: <b>{orders}</b>",
    )


@router.message(F.text == "⭐️ Модерация отзывов")
async def moderation_list(message: Message, session: AsyncSession):
    if message.from_user.id != ADMIN_ID:
        return
    reviews = await get_pending_reviews(session)
    if not reviews:
        await message.answer("<b>✅ Нет отзывов на модерацию.</b>")
        return
    for r in reviews[:10]:
        stars = "⭐" * r.rating
        user_name = r.user.full_name if r.user else "Аноним"
        text = (
            f"<b>📝 Отзыв #{r.id}</b>\n"
            f"От: {user_name}\n"
            f"Оценка: {stars}\n"
            f"Текст: <i>{r.text}</i>"
        )
        await message.answer(text, reply_markup=moderation_keyboard(r.id))


@router.message(F.text == "🗑 Удалить отзывы")
async def all_reviews_list(message: Message, session: AsyncSession):
    if message.from_user.id != ADMIN_ID:
        return
    reviews = await get_all_reviews(session)
    if not reviews:
        await message.answer("<b>Нет отзывов.</b>")
        return
    for r in reviews[:20]:
        stars = "⭐" * r.rating
        status_map = {"pending": "⏳ модерация", "approved": "✅ одобрен", "rejected": "❌ отклонён"}
        user_name = r.user.full_name if r.user else "Аноним"
        text = (
            f"<b>📝 Отзыв #{r.id}</b>\n"
            f"От: {user_name}\n"
            f"Оценка: {stars}\n"
            f"Статус: {status_map.get(r.status, r.status)}\n"
            f"Текст: <i>{r.text[:100]}</i>"
        )
        await message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"mod:delete:{r.id}")]
            ]),
        )


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


@router.callback_query(F.data.startswith("mod:"))
async def moderate_review(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    parts = callback.data.split(":")
    action = parts[1]
    review_id = int(parts[2])

    if action == "approve":
        review = await approve_review(session, review_id)
        if review:
            await callback.message.edit_text(f"<b>✅ Отзыв #{review_id} одобрен.</b>")
    elif action == "reject":
        review = await reject_review(session, review_id)
        if review:
            await callback.message.edit_text(f"<b>❌ Отзыв #{review_id} отклонён.</b>")
    elif action == "delete":
        ok = await delete_review(session, review_id)
        if ok:
            await callback.message.edit_text(f"<b>🗑 Отзыв #{review_id} удалён.</b>")
        else:
            await callback.answer("Отзыв не найден", show_alert=True)
    await callback.answer()
