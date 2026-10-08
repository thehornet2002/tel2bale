from pyrogram.types import Message

from config import ADS_CHANNELS
from db.model_async import set_state
from handlers.handler_helpers.callback_helpers.decorators import admin_required
from utils.keyboards import build_cancel_reply_keyboard


@admin_required
async def set_join_ads(message: Message, user_id: int) -> None:
    await set_state(user_id, "enter_join_ads_channel")
    await message.reply_text(
        "لطفا ID کانال را وارد کنید (مثال: tel2bale):",
        reply_markup=build_cancel_reply_keyboard("🔙 انصراف و بازگشت به مدیریت")
    )


@admin_required
async def delete_join_ads(message: Message, user_id: int) -> None:
    await set_state(user_id, "enter_delete_join_ads")

    channels = "\n".join(ADS_CHANNELS) if ADS_CHANNELS else "کانالی تنظیم نشده است."
    await message.reply_text(
        f"شناسه یا نام کاربری کانال مورد نظر جهت حذف را وارد کنید:\n\n{channels}",
        reply_markup=build_cancel_reply_keyboard("🔙 انصراف و بازگشت به مدیریت")
    )
