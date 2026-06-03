from re import compile

from pyrogram import Client, filters
from pyrogram.types import Message

from db.model_async import (
    check_ban,
    get_state,
    is_user_exist,
)

from handlers.handler_helpers.message_helper import (
    add_admin_send_id,
    delete_admin_send_id,
    enter_ads_message,
    enter_bale_ban,
    enter_bale_id,
    enter_bale_unban,
    enter_delete_join_ads,
    enter_join_ads_channel,
    enter_telegram_ban,
    enter_telegram_unban,
    forward,
    send_message_chat_id,
    send_message_send_message,
    send_support_message,
    set_bale_token_bot,
    set_limit_all_send_volume,
    set_limit_send_id,
    set_limit_set_limit,
    set_profile_photo_send_photo,
    change_donation_link,

    #s3
    set_s3_access_key,
    set_s3_secret_key,
    set_s3_endpoint
)

from utils.filters import join_filter


SEND_MESSAGE_RE = compile(r"^send_message_\d+$")
SET_LIMIT_RE = compile(r"^set_limit_\d+$")


STATE_HANDLERS = {
    "home": forward,
    "enter_bale_id": enter_bale_id,
    "send_support_message": send_support_message,
    "set_bale_token_bot": set_bale_token_bot,
    "enter_bale_ban": enter_bale_ban,
    "enter_bale_unban": enter_bale_unban,
    "enter_telegram_ban": enter_telegram_ban,
    "enter_telegram_unban": enter_telegram_unban,
    "enter_join_ads_channel": enter_join_ads_channel,
    "enter_delete_join_ads": enter_delete_join_ads,
    "enter_ads_message": enter_ads_message,
    "send_message_chat_id": send_message_chat_id,
    "add_admin_send_id": add_admin_send_id,
    "delete_admin_send_id": delete_admin_send_id,
    "set_profile_photo_send_photo": set_profile_photo_send_photo,
    "set_limit_all_send_volume": set_limit_all_send_volume,
    "set_limit_send_id": set_limit_send_id,
    "change_donation_link": change_donation_link,
    #s3
    "set_s3_access_key": set_s3_access_key,
    "set_s3_secret_key": set_s3_secret_key,
    "set_s3_endpoint": set_s3_endpoint
}


@Client.on_message(
    filters.private
    & ~filters.command("start")
    & ~filters.command("help")
    & join_filter
)
async def handle_input(
    client: Client,
    message: Message
) -> None:

    user_id = message.from_user.id

    if not await is_user_exist(user_id):
        return

    if await check_ban(user_id):
        return

    state = await get_state(user_id)

    handler = STATE_HANDLERS.get(state)

    if handler:
        await handler(message, user_id)
        return

    if SEND_MESSAGE_RE.match(state):
        await send_message_send_message(
            message,
            user_id
        )
        return

    if SET_LIMIT_RE.match(state):
        await set_limit_set_limit(
            message,
            user_id
        )
        return