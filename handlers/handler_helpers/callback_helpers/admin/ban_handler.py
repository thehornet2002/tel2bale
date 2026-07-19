from pyrogram.types import Message

from db.model_async import set_state
from handlers.handler_helpers.callback_helpers.decorators import admin_required
from utils.keyboards import build_back_management_keyboard


@admin_required
async def ban_bale(message: Message, user_id: int) -> None:
    await set_state(user_id, "enter_bale_ban")
    await message.edit_text(
        "لطفا ID عددی بله فرد موردنظر را وارد کنید.",
        reply_markup=build_back_management_keyboard()
    )


@admin_required
async def unban_bale(message: Message, user_id: int) -> None:
    await set_state(user_id, "enter_bale_unban")
    await message.edit_text(
        "لطفا ID عددی بله فرد موردنظر را وارد کنید.",
        reply_markup=build_back_management_keyboard()
    )


@admin_required
async def ban_telegram(message: Message, user_id: int) -> None:
    await set_state(user_id, "enter_telegram_ban")
    await message.edit_text(
        "لطفا ID عددی تلگرام فرد موردنظر را وارد کنید.",
        reply_markup=build_back_management_keyboard()
    )


@admin_required
async def unban_telegram(message: Message, user_id: int) -> None:
    await set_state(user_id, "enter_telegram_unban")
    await message.edit_text(
        "لطفا ID عددی تلگرام فرد موردنظر را وارد کنید.",
        reply_markup=build_back_management_keyboard()
    )