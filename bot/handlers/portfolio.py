from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.queries import (
    get_all_portfolio,
    get_portfolio_categories,
    get_portfolio_by_category,
    get_portfolio_item,
)
from bot.keyboards.inline import back_to_menu_keyboard
from bot.utils import sanitize_html

router = Router()

CATEGORY_ICONS = {
    "боты": "🤖", "bots": "🤖",
    "сайты": "🌐", "websites": "🌐",
    "мобильные": "📱", "mobile": "📱",
    "веб": "🌐", "web": "🌐",
    "api": "⚙️",
    "дизайн": "🎨", "design": "🎨",
}


def _icon(cat: str) -> str:
    return CATEGORY_ICONS.get(cat.lower(), "📁")


@router.message(F.text == "📂 Портфолио")
async def portfolio_menu(message: Message, session: AsyncSession):
    categories = await get_portfolio_categories(session)
    all_items = await get_all_portfolio(session)

    if not all_items:
        await message.answer(
            "<b>📂 Портфолио</b>\n\nПока нет добавленных проектов.",
            reply_markup=back_to_menu_keyboard(),
        )
        return

    rows = []
    for cat in categories:
        rows.append([InlineKeyboardButton(text=f"{_icon(cat)} {cat}", callback_data=f"pfcat:{cat}")])
    rows.append([InlineKeyboardButton(text="📋 Все проекты", callback_data="pfcat:all")])
    rows.append([InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_menu")])

    await message.answer(
        f"<b>📂 Портфолио</b>\n\nВыберите раздел:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


@router.callback_query(F.data.startswith("pfcat:"))
async def category_selected(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()
    category = callback.data.split(":", 1)[1]

    if category == "all":
        items = await get_all_portfolio(session)
        title = "Все проекты"
    else:
        items = await get_portfolio_by_category(session, category)
        title = category

    if not items:
        await callback.message.edit_text(
            f"<b>{_icon(title)} {title}</b>\n\nВ этой категории пока нет проектов.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="pf_back")],
            ]),
        )
        return

    rows = []
    for item in items:
        rows.append([InlineKeyboardButton(text=f"📄 {item.title}", callback_data=f"pfview:{item.id}")])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="pf_back")])

    await callback.message.edit_text(
        f"<b>{_icon(title)} {title}</b>  ({len(items)})\n\nВыберите проект:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


@router.callback_query(F.data == "pf_back")
async def back_to_categories(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()
    categories = await get_portfolio_categories(session)
    all_items = await get_all_portfolio(session)

    if not all_items:
        await callback.message.edit_text("<b>📂 Портфолио</b>\n\nПока нет проектов.", reply_markup=None)
        return

    rows = []
    for cat in categories:
        rows.append([InlineKeyboardButton(text=f"{_icon(cat)} {cat}", callback_data=f"pfcat:{cat}")])
    rows.append([InlineKeyboardButton(text="📋 Все проекты", callback_data="pfcat:all")])
    rows.append([InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_menu")])

    await callback.message.edit_text(
        "<b>📂 Портфолио</b>\n\nВыберите раздел:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


@router.callback_query(F.data.startswith("pfview:"))
async def view_project(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()
    item_id = int(callback.data.split(":")[1])
    item = await get_portfolio_item(session, item_id)

    if not item:
        await callback.message.edit_text("Проект не найден.")
        return

    lines = [f"<b>📄 {sanitize_html(item.title)}</b>", ""]
    if item.category:
        lines.append(f"<i>Раздел: {_icon(item.category)} {sanitize_html(item.category)}</i>\n")
    lines.append(sanitize_html(item.description))
    if item.link:
        lines.append(f"\n🔗 <a href=\"{item.link}\">Ссылка на проект</a>")

    kb_rows = []
    if item.link:
        kb_rows.append([InlineKeyboardButton(text="🔗 Открыть проект", url=item.link)])
    kb_rows.append([InlineKeyboardButton(text="🔙 К списку", callback_data="pfcat:all")])
    kb_rows.append([InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_menu")])

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
        disable_web_page_preview=True,
    )
