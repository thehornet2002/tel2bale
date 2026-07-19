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
    """بررسی می‌کند که متن پیام حتما یک عدد باشد و آن را برمی‌گرداند."""
    if not message.text or not message.text.isdigit():
        await message.reply_text("لطفا فقط شناسه عددی ارسال کنید.")
        return None
    return int(message.text)