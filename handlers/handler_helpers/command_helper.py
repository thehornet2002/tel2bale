from pyrogram.types import Message

from config import HELP_TXT, START_TXT

from db.model_async import (
    add_user,
    check_admin,
    is_user_exist,
)

from utils.keyboards import (
    build_start_keyboard,
)


async def ensure_user(user_id: int) -> bool:
    """
    در صورت نبودن کاربر، آن را ایجاد می‌کند.
    خروجی: وضعیت ادمین بودن کاربر
    """

    if not await is_user_exist(user_id):
        await add_user(user_id)

    return await check_admin(user_id)


async def start(
    message: Message,
    user_id: int
) -> None:

    is_admin = await ensure_user(user_id)

    await message.reply_text(
        START_TXT,
        reply_markup=build_start_keyboard(
            is_admin
        )
    )


async def help(
    message: Message,
    user_id: int
) -> None:

    is_admin = await ensure_user(user_id)

    await message.reply_text(
        HELP_TXT,
        reply_markup=build_start_keyboard(
            is_admin
        )
    )