from pyrogram.types import Message

from db.model_async import set_state
from handlers.handler_helpers.callback_helpers.decorators import admin_required
from utils.keyboards import build_back_management_keyboard


@admin_required
async def set_limit_all(message: Message, user_id: int) -> None:
    await set_state(user_id, "set_limit_all_send_volume")
    await message.edit_text(
        "محدودیت دانلود (GB) را وارد کنید:",
        reply_markup=build_back_management_keyboard()
    )


@admin_required
async def set_limit(message: Message, user_id: int) -> None:
    await set_state(user_id, "set_limit_send_id")
    await message.edit_text(
        "ID عددی کاربر را وارد کنید:",
        reply_markup=build_back_management_keyboard()
    )