from pyrogram import Client
from pyrogram import filters
from pyrogram.types import Message
from db.model_acync import is_user_exist, add_user, check_admin
from config import START_TXT, HELP_TXT
from utils.keyboards import build_start_keyboard
from handlers.handler_helpers.command_helper import start, help

@Client.on_message(filters.command('start') & filters.private)
async def start_handle(client: Client, message: Message):
    user_id = int(message.from_user.id)
    await start(message, user_id)




@Client.on_message(filters.command('help') & filters.private)
async def help_handle(client: Client, message: Message):
    user_id = int(message.from_user.id)
    await help(message, user_id)
