"""
توابع و دکوریتورهای مشترک بین هندلرها.
این ماژول برای جلوگیری از تکرار کد (admin_only و get_valid_id) بین چند فایل هندلر ساخته شده.
"""
from functools import wraps
from pyrogram.types import Message
from db import model_async


def admin_only(func):
    """دکوریتور برای بررسی اینکه آیا کاربر ادمین هست یا خیر."""
    @wraps(func)
    async def wrapper(message: Message, user_id: int, *args, **kwargs):
        is_admin = await model_async.check_admin(user_id)
        if not is_admin:
            return  # ادمین نیست، هیچ کاری نکن (یا پیام خطای دسترسی بده)
        return await func(message, user_id, *args, **kwargs)
    return wrapper


async def get_valid_id(message: Message) -> int | None:
    """
    بررسی و استخراج شناسه عددی:
    1. انتخاب بومی کاربر (UsersShared)
    2. انتخاب بومی گروه/چت (ChatShared)
    3. ارسال دستی متن عددی
    """
    if getattr(message, "users_shared", None):
        users = message.users_shared.users
        if users:
            return users[0].id

    if getattr(message, "chat_shared", None):
        chat = message.chat_shared.chat
        if chat:
            return chat.id

    text = (message.text or "").strip()
    if not text or len(text) > 20 or not (text.isdigit() or (text.startswith("-") and text[1:].isdigit())):
        await message.reply_text("لطفا فقط شناسه عددی ارسال کنید یا از دکمه انتخاب استفاده کنید.")
        return None

    try:
        val = int(text)
        if not (-9223372036854775808 <= val <= 9223372036854775807):
            raise ValueError
        return val
    except ValueError:
        await message.reply_text("شناسه عددی وارد شده در محدوده معتبر نیست.")
        return None