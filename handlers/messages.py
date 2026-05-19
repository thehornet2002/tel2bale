from pyrogram import Client, filters
from pyrogram.types import Message
from db.model_acync import check_ban, is_user_exist, get_state
from handlers.handler_helpers.message_helper import enter_bale_id, enter_verify_code, send_support_message
from utils.filters import join_filter


@Client.on_message(filters.private & filters.text & ~filters.command('start') & ~filters.command('help') & join_filter)
async def handle_input(client: Client, message: Message):
    user_id = int(message.from_user.id)
    if not await is_user_exist(user_id):
        return
    if await check_ban(user_id):
        return
    state = await get_state(user_id)

    if state == 'enter_bale_id':
        await enter_bale_id(message, user_id)
    elif state == 'enter_verify_code':
        await enter_verify_code(message, user_id)
    elif state == 'send_support_message':
        await send_support_message(message, user_id)