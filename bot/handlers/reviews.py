import math

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.queries import get_approved_reviews, get_review_stats
from bot.keyboards.inline import pagination_keyboard, back_to_menu_keyboard
from bot.config import REVIEWS_PER_PAGE

router = Router()


def format_review(review) -> str:
    stars = "⭐" * review.rating + "☆" * (5 - review.rating)
    user_name = review.user.full_name if review.user else "Аноним"
    return (
        f"<b>{user_name}</b>  {stars}\n"
        f"<i>{review.text}</i>\n"
    )


@router.message(F.text == "⭐️ Отзывы")
async def reviews_list(message: Message, session: AsyncSession):
    avg, count = await get_review_stats(session)
    items, total = await get_approved_reviews(session, 0)
    total_pages = max(1, math.ceil(total / REVIEWS_PER_PAGE))

    header = f"<b>⭐️ Отзывы клиентов</b>\n"
    header += f"Средний рейтинг: {'⭐' * round(avg)} {avg:.1f} / 5.0  ({count} отзывов)\n\n"

    if not items:
        await message.answer(
            header + "<i>Пока нет отзывов. Будьте первым!</i>",
            reply_markup=back_to_menu_keyboard(),
        )
        return

    text = header
    for r in items:
        text += format_review(r) + "\n"

    kb = pagination_keyboard(0, total_pages, "rv")
    await message.answer(text.strip(), reply_markup=kb, disable_web_page_preview=True)


@router.callback_query(F.data.startswith("rv:"))
async def reviews_pagination(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()
    action = callback.data.split(":")[1]

    data = callback.message.text
    idx = data.find("стр. ")
    if idx == -1:
        return
    page_str = data[idx + len("стр. "):].split(")")[0]
    current, total = page_str.split("/")
    current, total = int(current) - 1, int(total)

    if action == "next":
        page = min(current + 1, total - 1)
    elif action == "prev":
        page = max(current - 1, 0)
    else:
        return

    avg, count = await get_review_stats(session)
    items, t = await get_approved_reviews(session, page)
    total_pages = max(1, math.ceil(t / REVIEWS_PER_PAGE))

    header = f"<b>⭐️ Отзывы клиентов</b>\n"
    header += f"Средний рейтинг: {'⭐' * round(avg)} {avg:.1f} / 5.0  ({count} отзывов)\n\n"

    text = header
    for r in items:
        text += format_review(r) + "\n"

    kb = pagination_keyboard(page, total_pages, "rv")
    await callback.message.edit_text(text.strip(), reply_markup=kb, disable_web_page_preview=True)
