from pyrogram.types import Message

from db.model_async import set_state
from handlers.handler_helpers.callback_helpers.decorators import admin_required
from utils.keyboards import build_cancel_reply_keyboard, build_request_user_keyboard


@admin_required
async def set_limit_all(message: Message, user_id: int) -> None:
    await set_state(user_id, "set_limit_all_send_volume")
    await message.reply_text(
        "محدودیت دانلود همگانی (GB) را وارد کنید:",
        reply_markup=build_cancel_reply_keyboard("🔙 انصراف و بازگشت به مدیریت")
    )


@admin_required
async def set_limit(message: Message, user_id: int) -> None:
    await set_state(user_id, "set_limit_send_id")
    await message.reply_text(
        "کاربر مورد نظر را انتخاب کنید یا ID عددی او را وارد کنید:",
        reply_markup=build_request_user_keyboard("👤 انتخاب کاربر (Choose a user)")
    )

