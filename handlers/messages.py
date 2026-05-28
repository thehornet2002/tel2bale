from pyrogram import Client, filters
from pyrogram.types import Message
from db.model_async import check_ban, is_user_exist, get_state
from handlers.handler_helpers.message_helper import enter_bale_id, enter_verify_code, send_support_message, enter_bale_ban, enter_bale_unban, enter_telegram_ban, enter_telegram_unban, enter_join_ads_channel, enter_delete_join_ads,enter_ads_message, send_message_chat_id, send_message_send_message, add_admin_send_id, delete_admin_send_id, set_profile_photo_send_photo, set_limit_all_send_volume, set_limit_send_id, set_limit_set_limit, forward
from utils.filters import join_filter
import re




@Client.on_message(filters.private & ~filters.command('start') & ~filters.command('help') & join_filter)
async def handle_input(client: Client, message: Message):
    user_id = int(message.from_user.id)
    if not await is_user_exist(user_id):
        return
    if await check_ban(user_id):
        return
    state = await get_state(user_id)

    if state == 'home':
        await forward(message, user_id)
    elif state == 'enter_bale_id':
        await enter_bale_id(message, user_id)
    elif state == 'enter_verify_code':
        await enter_verify_code(message, user_id)
    elif state == 'send_support_message':
        await send_support_message(message, user_id)
    elif state == 'enter_bale_ban':
        await enter_bale_ban(message, user_id)
    elif state == 'enter_bale_unban':
        await enter_bale_unban(message, user_id)
    elif state == 'enter_telegram_ban':
        await enter_telegram_ban(message, user_id)
    elif state == 'enter_telegram_unban':
        await enter_telegram_unban(message, user_id)
    elif state == 'enter_join_ads_channel':
        await enter_join_ads_channel(message, user_id)
    elif state == 'enter_delete_join_ads':
        await enter_delete_join_ads(message, user_id)
    elif state == 'enter_ads_message':
        await enter_ads_message(message, user_id)
    elif state == 'send_message_chat_id':
        await send_message_chat_id(message, user_id)
    elif bool(re.compile(r"^send_message_\d+$").match(state)):
        await send_message_send_message(message, user_id)
    elif state == 'add_admin_send_id':
        await add_admin_send_id(message, user_id)
    elif state == 'delete_admin_send_id':
        await delete_admin_send_id(message, user_id)
    elif state == 'set_profile_photo_send_photo':
        await set_profile_photo_send_photo(message, user_id)
    elif state == 'set_limit_all_send_volume':
        await set_limit_all_send_volume(message, user_id)
    elif state == 'set_limit_send_id':
        await set_limit_send_id(message, user_id)
    elif bool(re.compile(r"^set_limit_\d+$").match(state)):
        await set_limit_set_limit(message, user_id)