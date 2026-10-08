from pyrogram.types import Message, ReplyKeyboardRemove

from config import HELP_TXT, START_TXT
from db.model_async import (
    add_user,
    check_admin,
    is_user_exist,
    is_user_whitelisted,
)
from utils.keyboards import (
    build_management_keyboard,
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
    if not is_user_whitelisted(user_id):
        await message.reply_text("⛔ این ربات در حالت لیست سفید (Whitelist) قرار دارد و حساب شما مجاز نیست.")
        return

    is_admin = await ensure_user(user_id)

    if is_admin:
        await message.reply_text(
            START_TXT,
            reply_markup=build_management_keyboard()
        )
        return

    await message.reply_text(
        START_TXT,
        reply_markup=build_start_keyboard()
    )


async def help(
    message: Message,
    user_id: int
) -> None:
    if not is_user_whitelisted(user_id):
        await message.reply_text("⛔ این ربات در حالت لیست سفید (Whitelist) قرار دارد و حساب شما مجاز نیست.")
        return

    is_admin = await ensure_user(user_id)

    await message.reply_text(
        HELP_TXT,
        reply_markup=build_start_keyboard(is_admin)
    )

