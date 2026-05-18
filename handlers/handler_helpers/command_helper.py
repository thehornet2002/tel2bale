from pyrogram.types import Message
from db.model_acync import is_user_exist, add_user, check_admin
from utils.keyboards import build_start_keyboard
from config import START_TXT, HELP_TXT


async def start(message : Message, user_id):
    if await is_user_exist(user_id) == False:
        add_user(user_id)
    is_admin = await check_admin(user_id)
    await message.reply_text(
        START_TXT,
        reply_markup=build_start_keyboard(is_admin)
    )



async def help(message:Message, user_id):
    user_id = int(message.from_user.id)
    if await is_user_exist(user_id) == False:
        add_user(user_id)
    is_admin = await check_admin(user_id)
    await message.reply_text(
        HELP_TXT,
        reply_markup=build_start_keyboard(is_admin)
    )