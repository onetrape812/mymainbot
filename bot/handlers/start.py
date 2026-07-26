from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import ADMIN_ID
from bot.database.queries import get_or_create_user, get_approved_reviews, get_review_stats
from bot.keyboards.inline import (
    main_menu,
    admin_menu,
    back_to_menu_keyboard,
)

router = Router()


def _format_review(review) -> str:
    stars = "⭐" * review.rating + "☆" * (5 - review.rating)
    user_name = review.user.full_name if review.user else "Аноним"
    return f"<b>{user_name}</b>  {stars}\n<i>{review.text}</i>\n"


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, command: Command = None):
    await get_or_create_user(
        session, message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
    )

    args = message.text.split(maxsplit=1)
    deep = args[1] if len(args) > 1 else ""

    if deep == "reviews":
        avg, count = await get_review_stats(session)
        items, total = await get_approved_reviews(session, 0)
        header = "<b>⭐️ Отзывы клиентов</b>\n"
        header += f"Средний рейтинг: {'⭐' * round(avg)} {avg:.1f} / 5.0  ({count} отзывов)\n\n"
        if not items:
            text = header + "<i>Пока нет отзывов.</i>"
        else:
            text = header + "\n".join(_format_review(r) for r in items)
        await message.answer(text.strip(), reply_markup=back_to_menu_keyboard(), disable_web_page_preview=True)
        return

    if message.from_user.id == ADMIN_ID:
        await message.answer(
            f"<b>Добро пожаловать, {message.from_user.full_name}! 👋</b>\n\n"
            "Вы вошли как администратор. Используйте меню ниже.",
            reply_markup=admin_menu(),
        )
    else:
        await message.answer(
            f"<b>Привет, {message.from_user.full_name}! 👋</b>\n\n"
            "Я — бот-портфолио. Здесь вы можете:\n"
            "• Посмотреть мои работы\n"
            "• Прочитать отзывы клиентов\n"
            "• Оставить свой отзыв\n"
            "• Связаться со мной для заказа\n\n"
            "Выберите раздел:",
            reply_markup=main_menu(),
        )


@router.callback_query(F.data == "back_to_menu")
async def cb_back_to_menu(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()
    if callback.from_user.id == ADMIN_ID:
        await callback.message.edit_text(
            "<b>Админ-панель</b>\nВыберите действие:",
            reply_markup=None,
        )
    else:
        await callback.message.edit_text(
            "<b>Главное меню</b>\nВыберите раздел:",
            reply_markup=None,
        )


@router.message(F.text == "ℹ️ Обо мне")
async def about_me(message: Message):
    text = (
        "👨‍💻 <b>ОБО МНЕ / ABOUT ME</b>\n"
        "Привет! Я <b>onetrape</b> — разработчик бэкенда и специалист по автоматизации.\n\n"
        "Моя главная специализация — экономить ваше время и ресурсы с помощью понятного, надежного и поддерживаемого кода.\n\n"
        "<b>🧠 МОИ ПРИНЦИПЫ В РАБОТЕ:</b>\n"
        "• <b>Прагматизм:</b> Не усложняю там, где нужно простое решение, но закладываю запас прочности там, где проект будет расти.\n"
        "• <b>Прозрачность:</b> Всегда на связи, объясняю сложные технические моменты простым языком без лишней терминологии.\n"
        "• <b>Чистый код:</b> Пишу так, чтобы через год софт работало так же стабильно, а логика оставалась понятной.\n\n"
        "<b>🛠 ОСНОВНОЙ СТЕК:</b>\n"
        "<code>Python</code> · <code>aiogram 3.x</code> · <code>SQLAlchemy</code> · <code>PostgreSQL</code> · <code>C++</code> · <code>Java</code> · <code>Docker</code> · <code>REST API</code>\n\n"
        "<blockquote>Никакой магии и пустых обещаний — только чистая логика, работающий функционал и дедлайны, которые соблюдаются.</blockquote>"
    )
    await message.answer(text, reply_markup=back_to_menu_keyboard())


@router.message(F.text == "👤 Как пользователь")
async def switch_to_user_mode(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        "Переключился на пользовательский режим.",
        reply_markup=main_menu(),
    )
