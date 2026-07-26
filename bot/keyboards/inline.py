from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from bot.config import ADMIN_ID, BOT_USERNAME, OWNER_USERNAME


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📂 Портфолио")],
            [KeyboardButton(text="⭐️ Отзывы"), KeyboardButton(text="✍️ Оставить отзыв")],
            [KeyboardButton(text="💬 Заказать"), KeyboardButton(text="ℹ️ Обо мне")],
        ],
        resize_keyboard=True,
    )


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="📢 Создать пост")],
            [KeyboardButton(text="📂 Управление портфолио")],
            [KeyboardButton(text="⭐️ Модерация отзывов")],
            [KeyboardButton(text="🗑 Удалить отзывы")],
            [KeyboardButton(text="👤 Как пользователь")],
        ],
        resize_keyboard=True,
    )


def rating_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1 ⭐", callback_data="rate:1"),
                InlineKeyboardButton(text="2 ⭐", callback_data="rate:2"),
                InlineKeyboardButton(text="3 ⭐", callback_data="rate:3"),
                InlineKeyboardButton(text="4 ⭐", callback_data="rate:4"),
                InlineKeyboardButton(text="5 ⭐", callback_data="rate:5"),
            ]
        ]
    )


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="review_confirm"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="review_cancel"),
            ]
        ]
    )


def pagination_keyboard(page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    buttons = []
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"{prefix}:prev"))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"{prefix}:next"))
    buttons.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def moderation_keyboard(review_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"mod:approve:{review_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"mod:reject:{review_id}"),
            ],
            [
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"mod:delete:{review_id}"),
            ],
        ]
    )


def admin_portfolio_list_keyboard(items: list, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    total_pages = max(1, -(-len(items) // per_page))
    start = page * per_page
    end = start + per_page
    page_items = items[start:end]

    buttons = []
    for item in page_items:
        buttons.append([InlineKeyboardButton(text=f"🗑 {item.title}", callback_data=f"apf:del:{item.id}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"apf:page:{page - 1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"apf:page:{page + 1}"))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton(text="➕ Добавить проект", callback_data="apf:add")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def post_buttons_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 Заказать бота", callback_data="post_btn:order"),
                InlineKeyboardButton(text="⭐️ Отзывы", callback_data="post_btn:reviews"),
            ],
            [InlineKeyboardButton(text="➡️ Далее", callback_data="post_btn:next")],
        ]
    )


def post_preview_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Опубликовать", callback_data="post_publish"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="post_cancel"),
            ]
        ]
    )


def contact_keyboard() -> InlineKeyboardMarkup:
    owner = OWNER_USERNAME or "alcotarget"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📩 Написать напрямую", url=f"https://t.me/{owner}")],
            [InlineKeyboardButton(text="📝 Оформить заказ", callback_data="order_start")],
        ]
    )


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_menu")]
        ]
    )


def admin_confirm_portfolio_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Сохранить", callback_data="apf:confirm"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="apf:cancel"),
            ]
        ]
    )


def order_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="order_confirm"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="order_cancel"),
            ]
        ]
    )
