from pyrogram.types import Message

from db.model_async import set_state
from handlers.handler_helpers.callback_helpers.decorators import admin_required
from utils.keyboards import build_back_management_keyboard


@admin_required
async def send_ads_message(message: Message, user_id: int) -> None:
    await set_state(user_id, "enter_ads_message")
    await message.edit_text(
        "پیام همگانی را وارد کنید:",
        reply_markup=build_back_management_keyboard()
    )


@admin_required
async def send_message(message: Message, user_id: int) -> None:
    await set_state(user_id, "send_message_chat_id")
    await message.edit_text(
        "ID عددی تلگرام کاربر را وارد کنید:",
        reply_markup=build_back_management_keyboard()
    )