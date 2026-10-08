"""
Shared utility decorators and ID extraction helpers.
"""
from functools import wraps
from pyrogram.types import Message
from db import model_async


def admin_only(func):
    """Decorator to verify if caller is an administrator."""
    @wraps(func)
    async def wrapper(message: Message, user_id: int, *args, **kwargs):
        is_admin = await model_async.check_admin(user_id)
        if not is_admin:
            return
        return await func(message, user_id, *args, **kwargs)
    return wrapper


async def get_valid_id(message: Message) -> int | None:
    """
    Extract numeric identifier from:
    1. UsersShared native picker
    2. ChatShared native picker
    3. Manual integer text input
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
