from pyrogram.types import Message

from db.model_async import set_state
from handlers.handler_helpers.callback_helpers.decorators import admin_required
from utils.keyboards import build_cancel_reply_keyboard, build_request_user_keyboard


@admin_required
async def send_ads_message(message: Message, user_id: int) -> None:
    await set_state(user_id, "enter_ads_message")
    await message.reply_text(
        "پیام تبلیغاتی همگانی را وارد کنید:",
        reply_markup=build_cancel_reply_keyboard("🔙 انصراف و بازگشت به مدیریت")
    )


@admin_required
async def send_message(message: Message, user_id: int) -> None:
    await set_state(user_id, "send_message_chat_id")
    await message.reply_text(
        "کاربر مورد نظر را انتخاب کنید یا ID عددی تلگرام او را وارد کنید:",
        reply_markup=build_request_user_keyboard("👤 انتخاب کاربر (Choose a user)")
    )

