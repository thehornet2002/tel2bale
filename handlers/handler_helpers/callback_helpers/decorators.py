from functools import wraps

from pyrogram.types import Message

from db.model_async import check_admin


def admin_required(func):
    @wraps(func)
    async def wrapper(message: Message, user_id: int, *args, **kwargs):
        if not await check_admin(user_id):
            return

        return await func(message, user_id, *args, **kwargs)

    return wrapper