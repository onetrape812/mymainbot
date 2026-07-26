from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

from bot.config import ADMIN_ID, CHANNEL_ID, BOT_USERNAME, OWNER_USERNAME
from bot.states.states import PostBuilderState
from bot.keyboards.inline import back_to_menu_keyboard

router = Router()

PREDEFINED = {
    "order": ("📝 Оформить заказ", f"https://t.me/{OWNER_USERNAME}" if OWNER_USERNAME else "https://t.me/"),
    "reviews": ("⭐️ Отзывы", f"https://t.me/{BOT_USERNAME}?start=reviews" if BOT_USERNAME else "https://t.me/"),
}


def _build_buttons_keyboard(chosen_predefined: list[str], custom: list[dict]) -> InlineKeyboardMarkup:
    rows = []

    order_selected = "✅ " if "order" in chosen_predefined else ""
    reviews_selected = "✅ " if "reviews" in chosen_predefined else ""
    rows.append([InlineKeyboardButton(text=f"{order_selected}📝 Оформить заказ", callback_data="post_btn:order")])
    rows.append([InlineKeyboardButton(text=f"{reviews_selected}⭐️ Отзывы", callback_data="post_btn:reviews")])

    for i, cb in enumerate(custom):
        rows.append([InlineKeyboardButton(text=f"🗑 {cb['text']}", callback_data=f"post_btn:delc:{i}")])

    rows.append([InlineKeyboardButton(text="➕ Своя кнопка", callback_data="post_btn:addcustom")])
    rows.append([InlineKeyboardButton(text="➡️ Готово", callback_data="post_btn_done")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def _preview_text(chosen_predefined: list[str], custom: list[dict]) -> str:
    if not chosen_predefined and not custom:
        return "<i>Пока нет кнопок.</i>"
    lines = []
    for key in chosen_predefined:
        text, url = PREDEFINED[key]
        lines.append(f"• <b>{text}</b>")
    for cb in custom:
        lines.append(f"• <b>{cb['text']}</b>")
    return "\n".join(lines)


@router.message(F.text == "📢 Создать пост")
async def start_post(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await message.answer(
        "<b>📢 Генератор постов</b>\n\n"
        "Шаг 1/3: Отправьте текст поста.\n"
        "Поддерживается HTML-разметка: <b>&lt;b&gt;</b>, <i>&lt;i&gt;</i>, <code>&lt;code&gt;</code>, "
        "<a href=\"...\">&lt;a&gt;</a>\n\n"
        "Чтобы добавить заголовок, напишите его первой строкой.\n"
        "Отправьте <b>/cancel</b> для отмены.",
    )
    await state.set_state(PostBuilderState.text)


@router.message(PostBuilderState.text)
async def post_text(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Отправьте текстовый пост:")
        return
    await state.update_data(text=message.text)
    await message.answer(
        "Шаг 2/3: Отправьте фото или видео для поста.\n"
        "Или нажмите <b>«Пропустить»</b> для текстового поста.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏩ Пропустить", callback_data="post_skip_media")]
        ]),
    )
    await state.set_state(PostBuilderState.media)


@router.callback_query(F.data == "post_skip_media", PostBuilderState.media)
async def skip_media(callback: CallbackQuery, state: FSMContext):
    await state.update_data(media=None, media_type=None, chosen_predefined=[], custom_buttons=[])
    kb = _build_buttons_keyboard([], [])
    await callback.message.edit_text(
        "<b>Шаг 3/3: Inline-кнопки</b>\n\n"
        "Нажмите на кнопку чтобы включить/выключить её.\n"
        "«➕ Своя кнопка» — добавить свою с произвольным текстом и ссылкой.\n"
        "Когда всё готово — «➡️ Готово».",
        reply_markup=kb,
    )
    await callback.answer()
    await state.set_state(PostBuilderState.buttons)


@router.message(PostBuilderState.media)
async def post_media(message: Message, state: FSMContext):
    if message.photo:
        file_id = message.photo[-1].file_id
        await state.update_data(media=file_id, media_type="photo")
    elif message.video:
        file_id = message.video.file_id
        await state.update_data(media=file_id, media_type="video")
    else:
        await message.answer("Отправьте фото, видео или нажмите «Пропустить»:")
        return

    await state.update_data(chosen_predefined=[], custom_buttons=[])
    kb = _build_buttons_keyboard([], [])
    await message.answer(
        "<b>Шаг 3/3: Inline-кнопки</b>\n\n"
        "Нажмите на кнопку чтобы включить/выключить её.\n"
        "«➕ Своя кнопка» — добавить свою с произвольным текстом и ссылкой.\n"
        "Когда всё готово — «➡️ Готово».",
        reply_markup=kb,
    )
    await state.set_state(PostBuilderState.buttons)


@router.callback_query(F.data.startswith("post_btn:"), PostBuilderState.buttons)
async def button_toggle(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    action = parts[1]

    if action == "delc":
        idx = int(parts[2])
        data = await state.get_data()
        custom = data.get("custom_buttons", [])
        if 0 <= idx < len(custom):
            custom.pop(idx)
        await state.update_data(custom_buttons=custom)
        kb = _build_buttons_keyboard(data.get("chosen_predefined", []), custom)
        try:
            await callback.message.edit_reply_markup(reply_markup=kb)
        except Exception:
            pass
        await callback.answer("Удалено")
        return

    if action in ("order", "reviews"):
        data = await state.get_data()
        chosen = data.get("chosen_predefined", [])
        if action in chosen:
            chosen.remove(action)
        else:
            if len(chosen) + len(data.get("custom_buttons", [])) >= 2:
                await callback.answer("Максимум 2 кнопки!", show_alert=True)
                return
            chosen.append(action)
        await state.update_data(chosen_predefined=chosen)
        kb = _build_buttons_keyboard(chosen, data.get("custom_buttons", []))
        try:
            await callback.message.edit_reply_markup(reply_markup=kb)
        except Exception:
            pass
        await callback.answer()
        return

    if action == "addcustom":
        data = await state.get_data()
        total = len(data.get("chosen_predefined", [])) + len(data.get("custom_buttons", []))
        if total >= 2:
            await callback.answer("Максимум 2 кнопки!", show_alert=True)
            return
        await callback.message.edit_text(
            "<b>Добавление своей кнопки</b>\n\n"
            "Отправьте в формате:\n"
            "<code>Текст кнопки | https://ссылка</code>",
        )
        await callback.answer()
        await state.set_state(PostBuilderState.button_text)
        return

    await callback.answer()


@router.message(PostBuilderState.button_text)
async def custom_button_input(message: Message, state: FSMContext):
    if not message.text or "|" not in message.text:
        await message.answer(
            "Неверный формат. Отправьте:\n<code>Текст кнопки | https://ссылка</code>"
        )
        return

    parts = message.text.split("|", 1)
    btn_text = parts[0].strip()
    btn_url = parts[1].strip()

    if not btn_text or not btn_url.startswith("http"):
        if btn_url.startswith("@"):
            btn_url = f"https://t.me/{btn_url[1:]}"
        elif btn_url:
            btn_url = f"https://{btn_url}"
        else:
            await message.answer("Текст не может быть пустым, URL должен начинаться с http. Попробуйте ещё раз:")
            return

    data = await state.get_data()
    custom = data.get("custom_buttons", [])
    total = len(data.get("chosen_predefined", [])) + len(custom)

    if total >= 2:
        await message.answer("Максимум 2 кнопки. Нажмите «➡️ Готово».")
        return

    custom.append({"text": btn_text, "url": btn_url})
    await state.update_data(custom_buttons=custom)

    kb = _build_buttons_keyboard(data.get("chosen_predefined", []), custom)
    await message.answer(
        f"✅ Кнопка <b>«{btn_text}»</b> добавлена.\n\nВыбирайте дальше или нажмите «➡️ Готово».",
        reply_markup=kb,
    )
    await state.set_state(PostBuilderState.buttons)


@router.callback_query(F.data == "post_btn_done", PostBuilderState.buttons)
async def finish_buttons(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    data = await state.get_data()
    chosen_pre = data.get("chosen_predefined", [])
    custom = data.get("custom_buttons", [])

    all_buttons = []
    for key in chosen_pre:
        if key in PREDEFINED:
            text, url = PREDEFINED[key]
            all_buttons.append({"text": text, "url": url})
    all_buttons.extend(custom)

    if not all_buttons:
        await callback.message.edit_text("Пост без кнопок. Отправляю предпросмотр...", reply_markup=None)
    else:
        await callback.message.edit_text(
            f"Кнопки готовы:\n{_preview_text(chosen_pre, custom)}\n\nОтправляю предпросмотр в канал...",
            reply_markup=None,
        )

    channel_kb_rows = [[InlineKeyboardButton(text=b["text"], url=b["url"])] for b in all_buttons]
    channel_reply_markup = InlineKeyboardMarkup(inline_keyboard=channel_kb_rows) if channel_kb_rows else None

    channel_msg = None
    if data.get("media") and data.get("media_type") == "photo":
        channel_msg = await bot.send_photo(
            CHANNEL_ID, data["media"],
            caption=data["text"],
            parse_mode=ParseMode.HTML,
            reply_markup=channel_reply_markup,
        )
    elif data.get("media") and data.get("media_type") == "video":
        channel_msg = await bot.send_video(
            CHANNEL_ID, data["media"],
            caption=data["text"],
            parse_mode=ParseMode.HTML,
            reply_markup=channel_reply_markup,
        )
    else:
        channel_msg = await bot.send_message(
            CHANNEL_ID, data["text"],
            parse_mode=ParseMode.HTML,
            reply_markup=channel_reply_markup,
        )

    await state.update_data(channel_msg_id=channel_msg.message_id)

    publish_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Опубликовать", callback_data="post_publish"),
         InlineKeyboardButton(text="❌ Отмена", callback_data="post_cancel")],
    ])
    await callback.message.answer(
        "✅ Пост отправлен в канал.\n"
        "Нажмите «🚀 Опубликовать» чтобы оставить, или «❌ Отмена» чтобы удалить.",
        reply_markup=publish_kb,
    )
    await state.set_state(PostBuilderState.preview)


@router.callback_query(F.data == "post_publish", PostBuilderState.preview)
async def publish_post(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.message.edit_text("<b>🚀 Пост опубликован!</b>", reply_markup=back_to_menu_keyboard())
    await callback.answer()
    await state.clear()


@router.callback_query(F.data == "post_cancel", PostBuilderState.preview)
async def cancel_post(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    msg_id = data.get("channel_msg_id")
    if msg_id and CHANNEL_ID:
        try:
            await bot.delete_message(CHANNEL_ID, msg_id)
        except Exception:
            pass
    await callback.message.edit_text("Публикация отменена.", reply_markup=back_to_menu_keyboard())
    await callback.answer()
    await state.clear()
