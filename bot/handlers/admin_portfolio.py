from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import ADMIN_ID
from bot.states.states import AdminPortfolioState
from bot.database.queries import get_all_portfolio, add_portfolio_item, delete_portfolio_item
from bot.keyboards.inline import admin_portfolio_list_keyboard, admin_confirm_portfolio_keyboard, back_to_menu_keyboard
from bot.utils import sanitize_html

router = Router()


@router.message(F.text == "📂 Управление портфолио")
async def admin_portfolio(message: Message, session: AsyncSession):
    if message.from_user.id != ADMIN_ID:
        return
    items = await get_all_portfolio(session)
    if not items:
        await message.answer(
            "<b>📂 Портфолио пусто.</b>\n\nНажмите «➕ Добавить проект» для начала.",
            reply_markup=admin_portfolio_list_keyboard([], 0),
        )
        return
    text = f"<b>📂 Проекты в портфолио ({len(items)}):</b>\n\n"
    for i, item in enumerate(items, 1):
        text += f"{i}. <b>{item.title}</b> — <i>{item.category or 'Без категории'}</i>\n"
    await message.answer(text, reply_markup=admin_portfolio_list_keyboard(items, 0))


@router.callback_query(F.data == "apf:add")
async def add_portfolio_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.edit_text(
        "<b>➕ Новый проект</b>\n\nВведите название проекта:",
        reply_markup=None,
    )
    await callback.answer()
    await state.set_state(AdminPortfolioState.title)


@router.message(AdminPortfolioState.title)
async def add_portfolio_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Описание проекта:")
    await state.set_state(AdminPortfolioState.description)


@router.message(AdminPortfolioState.description)
async def add_portfolio_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Ссылка на проект (или «-» если нет):")
    await state.set_state(AdminPortfolioState.link)


@router.message(AdminPortfolioState.link)
async def add_portfolio_link(message: Message, state: FSMContext):
    link = message.text.strip() if message.text and message.text.strip() != "-" else None
    if link and not link.startswith("http"):
        if link.startswith("@"):
            link = f"https://t.me/{link[1:]}"
        else:
            link = f"https://{link}"
    await state.update_data(link=link)
    await message.answer("Категория (например: боты, веб, мобильные):")
    await state.set_state(AdminPortfolioState.category)


@router.message(AdminPortfolioState.category)
async def add_portfolio_category(message: Message, state: FSMContext):
    category = message.text if message.text and message.text != "-" else None
    await state.update_data(category=category)
    data = await state.get_data()
    preview = (
        f"<b>📋 Предпросмотр проекта:</b>\n\n"
        f"<b>Название:</b> {sanitize_html(data['title'])}\n"
        f"<b>Описание:</b> {sanitize_html(data['description'])}\n"
        f"<b>Ссылка:</b> {data.get('link') or 'нет'}\n"
        f"<b>Категория:</b> {data.get('category') or 'нет'}\n\n"
        "Сохранить?"
    )
    await message.answer(preview, reply_markup=admin_confirm_portfolio_keyboard())
    await state.set_state(AdminPortfolioState.confirm)


@router.callback_query(F.data == "apf:confirm", AdminPortfolioState.confirm)
async def save_portfolio(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await add_portfolio_item(session, data["title"], data["description"], data.get("link"), data.get("category"))
    await callback.message.edit_text(
        "<b>✅ Проект добавлен в портфолио!</b>",
        reply_markup=back_to_menu_keyboard(),
    )
    await callback.answer()
    await state.clear()


@router.callback_query(F.data == "apf:cancel")
async def cancel_add_portfolio(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Добавление проекта отменено.", reply_markup=back_to_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("apf:del:"))
async def delete_portfolio(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id != ADMIN_ID:
        return
    item_id = int(callback.data.split(":")[2])
    ok = await delete_portfolio_item(session, item_id)
    if ok:
        await callback.answer("✅ Проект удалён", show_alert=True)
    else:
        await callback.answer("Проект не найден", show_alert=True)

    items = await get_all_portfolio(session)
    if items:
        text = f"<b>📂 Проекты в портфолио ({len(items)}):</b>\n\n"
        for i, item in enumerate(items, 1):
            text += f"{i}. <b>{item.title}</b> — <i>{item.category or 'Без категории'}</i>\n"
        await callback.message.edit_text(text, reply_markup=admin_portfolio_list_keyboard(items, 0))
    else:
        await callback.message.edit_text(
            "<b>📂 Портфолио пусто.</b>",
            reply_markup=admin_portfolio_list_keyboard([], 0),
        )


@router.callback_query(F.data.startswith("apf:page:"))
async def portfolio_page_nav(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id != ADMIN_ID:
        return
    page = int(callback.data.split(":")[2])
    items = await get_all_portfolio(session)
    if not items:
        return
    text = f"<b>📂 Проекты в портфолио ({len(items)}):</b>\n\n"
    for i, item in enumerate(items, 1):
        text += f"{i}. <b>{item.title}</b> — <i>{item.category or 'Без категории'}</i>\n"
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=admin_portfolio_list_keyboard(items, page))
