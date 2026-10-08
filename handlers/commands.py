from pyrogram import Client
from pyrogram import filters
from pyrogram.types import Message
from db.model_async import is_user_exist, add_user, check_admin, set_state
from config import START_TXT, HELP_TXT
from utils.keyboards import build_start_keyboard, build_management_keyboard
from handlers.handler_helpers.command_helper import start, help
from utils.filters import join_filter, user_limit_filter, whitelist_filter

@Client.on_message(filters.command('start') & filters.private & join_filter & user_limit_filter & whitelist_filter)
async def start_handle(client: Client, message: Message):
    user_id = int(message.from_user.id)
    await start(message, user_id)




@Client.on_message(filters.command('help') & filters.private & join_filter & whitelist_filter)
async def help_handle(client: Client, message: Message):
    user_id = int(message.from_user.id)
    await help(message, user_id)


@Client.on_message(filters.command(['admin', 'panel']) & filters.private & whitelist_filter)
async def panel_handle(client: Client, message: Message):
    user_id = int(message.from_user.id)
    if not await check_admin(user_id):
        return
    await set_state(user_id, "management")
    await message.reply_text("⚙️ پنل مدیریت:", reply_markup=build_management_keyboard())

