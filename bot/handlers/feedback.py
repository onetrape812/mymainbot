from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import ADMIN_ID, MAX_REVIEW_LENGTH
from bot.states.states import ReviewState
from bot.database.queries import add_review
from bot.keyboards.inline import (
    rating_keyboard,
    confirm_keyboard,
    back_to_menu_keyboard,
)
from bot.keyboards.inline import main_menu as main_menu_kb

router = Router()


@router.message(F.text == "✍️ Оставить отзыв")
async def start_review(message: Message, state: FSMContext):
    await message.answer(
        "<b>✍️ Оставить отзыв</b>\n\n"
        "Оцените качество услуг по 5-балльной шкале:",
        reply_markup=rating_keyboard(),
    )
    await state.set_state(ReviewState.rating)


@router.callback_query(F.data.startswith("rate:"), ReviewState.rating)
async def set_rating(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split(":")[1])
    await state.update_data(rating=rating)
    await callback.message.edit_text(
        f"<b>Оценка:</b> {'⭐' * rating}\n\n"
        "Напишите текст вашего отзыва (до 1000 символов):",
        reply_markup=None,
    )
    await callback.answer()
    await state.set_state(ReviewState.text)


@router.message(ReviewState.text)
async def set_text(message: Message, state: FSMContext):
    text = message.text or ""
    if len(text) > MAX_REVIEW_LENGTH:
        await message.answer(
            f"Текст слишком длинный ({len(text)} символов). "
            f"Максимум — {MAX_REVIEW_LENGTH}. Попробуйте ещё раз:"
        )
        return
    if not text.strip():
        await message.answer("Отзыв не может быть пустым. Напишите текст:")
        return

    await state.update_data(text=text)
    data = await state.get_data()
    stars = "⭐" * data["rating"]
    preview = (
        f"<b>Предпросмотр отзыва:</b>\n\n"
        f"Оценка: {stars}\n"
        f"Текст: <i>{data['text']}</i>\n\n"
        "Отправить?"
    )
    await message.answer(preview, reply_markup=confirm_keyboard())
    await state.set_state(ReviewState.confirm)


@router.callback_query(F.data == "review_confirm", ReviewState.confirm)
async def confirm_review(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    review = await add_review(session, callback.from_user.id, data["rating"], data["text"])

    stars = "⭐" * data["rating"]
    await callback.message.edit_text(
        "<b>✅ Спасибо!</b>\n\nВаш отзыв отправлен на модерацию. "
        "После проверки он появится в разделе «Отзывы».",
        reply_markup=back_to_menu_keyboard(),
    )
    await callback.answer()
    await state.clear()

    admin_text = (
        f"<b>📝 Новый отзыв на модерацию</b>\n\n"
        f"От: {callback.from_user.full_name} (@{callback.from_user.username or 'нет'})\n"
        f"Оценка: {stars}\n"
        f"Текст: <i>{data['text']}</i>"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"mod:approve:{review.id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"mod:reject:{review.id}"),
    ]])
    try:
        await callback.bot.send_message(ADMIN_ID, admin_text, reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data == "review_cancel", ReviewState.confirm)
@router.callback_query(F.data == "review_cancel")
async def cancel_review(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Отзыв отменён.", reply_markup=back_to_menu_keyboard())
    await callback.answer()
