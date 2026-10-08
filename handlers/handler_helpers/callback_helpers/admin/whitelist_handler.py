from pyrogram.types import Message
from db.model_async import (
    get_whitelist_users,
    is_whitelist_enabled,
    set_state,
    set_whitelist_enabled,
)
from handlers.handler_helpers.callback_helpers.decorators import admin_required
from utils.keyboards import (
    build_request_user_keyboard,
    build_whitelist_reply_keyboard,
)


@admin_required
async def manage_whitelist(message: Message, user_id: int) -> None:
    await set_state(user_id, "manage_whitelist")
    enabled = is_whitelist_enabled()
    text = (
        "🛡️ **مدیریت لیست سفید (Whitelist)**\n\n"
        f"وضعیت فعلی: {'🟢 فعال' if enabled else '🔴 غیرفعال'}\n"
        "در صورت فعال بودن لیست سفید، فقط کاربران موجود در لیست سفید و ادمین‌ها اجازه استفاده از ربات را دارند."
    )
    if getattr(message, "outgoing", False) or getattr(getattr(message, "from_user", None), "is_self", False):
        try:
            await message.edit_text("✅ وارد بخش لیست سفید شدید.")
        except Exception:
            pass
    await message.reply_text(text, reply_markup=build_whitelist_reply_keyboard(enabled))


@admin_required
async def toggle_whitelist(message: Message, user_id: int) -> None:
    new_status = not is_whitelist_enabled()
    await set_whitelist_enabled(new_status)
    await manage_whitelist(message, user_id)


@admin_required
async def add_whitelist(message: Message, user_id: int) -> None:
    await set_state(user_id, "add_whitelist_send_id")
    await message.reply_text(
        "لطفا با استفاده از دکمه زیر کاربر مورد نظر را انتخاب کنید یا شناسه عددی تلگرام او را ارسال نمایید:",
        reply_markup=build_request_user_keyboard("👤 انتخاب کاربر برای لیست سفید (Choose a user)")
    )


@admin_required
async def remove_whitelist(message: Message, user_id: int) -> None:
    await set_state(user_id, "remove_whitelist_send_id")
    await message.reply_text(
        "لطفا با استفاده از دکمه زیر کاربر مورد نظر را برای حذف انتخاب کنید یا شناسه عددی او را ارسال نمایید:",
        reply_markup=build_request_user_keyboard("👤 انتخاب کاربر جهت حذف (Choose a user)")
    )


@admin_required
async def list_whitelist(message: Message, user_id: int) -> None:
    users = get_whitelist_users()
    if not users:
        text = "📋 لیست سفید در حال حاضر خالی است."
    else:
        text = "📋 **کاربران موجود در لیست سفید:**\n\n" + "\n".join(f"- `{u}`" for u in users)

    await message.reply_text(text, reply_markup=build_whitelist_reply_keyboard(is_whitelist_enabled()))

