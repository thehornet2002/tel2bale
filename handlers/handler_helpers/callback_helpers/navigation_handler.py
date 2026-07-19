from pyrogram.types import Message

from config import HELP_TXT, START_TXT
from db.model_async import add_user, check_admin, is_user_exist, set_state
from utils.filters import has_user_capacity
from utils.keyboards import build_start_keyboard


async def start(message: Message, user_id: int) -> None:
    if not await is_user_exist(user_id):
        if not await has_user_capacity(user_id):
            await message.edit_text(
                "ظرفیت ثبت‌نام کاربران جدید در ربات تکمیل شده است."
            )
            return
        await add_user(user_id)

    await message.edit_text(
        START_TXT,
        reply_markup=build_start_keyboard(await check_admin(user_id))
    )


async def back(message: Message, user_id: int) -> None:
    await set_state(user_id, "home")

    await message.edit_text(
        START_TXT,
        reply_markup=build_start_keyboard(await check_admin(user_id))
    )


async def help(message: Message, user_id: int) -> None:
    await set_state(user_id, "home")

    await message.edit_text(
        HELP_TXT,
        reply_markup=build_start_keyboard(await check_admin(user_id))
    )