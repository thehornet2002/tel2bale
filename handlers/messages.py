from re import compile

from pyrogram import Client, filters
from pyrogram.types import Message

from db.model_async import check_ban, get_state, is_user_exist

from handlers.handler_helpers.message_helpers.admin_handler import (
    add_admin_send_id,
    change_donation_link,
    delete_admin_send_id,
    enter_bale_ban,
    enter_bale_unban,
    enter_telegram_ban,
    enter_telegram_unban,
    set_support_group_send_id,
    set_max_users_send_value,
    set_max_active_users_send_value,
)
from handlers.handler_helpers.message_helpers.ads_handler import (
    enter_delete_join_ads,
    enter_join_ads_channel,
)
from handlers.handler_helpers.message_helpers.forward_handler import forward
from handlers.handler_helpers.message_helpers.limit_handler import (
    set_limit_all_send_volume,
    set_limit_send_id,
    set_limit_set_limit,
)
from handlers.handler_helpers.message_helpers.messaging_handler import (
    enter_ads_message,
    send_message_chat_id,
    send_message_send_message,
)
from handlers.handler_helpers.message_helpers.s3_handler import (
    set_s3_access_key,
    set_s3_endpoint,
    set_s3_secret_key,
)
from handlers.handler_helpers.message_helpers.user_handler import (
    enter_bale_id,
    send_support_message,
    set_bale_token_bot,
)
from handlers.handler_helpers.message_helpers.support_handler import handle_support_reply
from utils.filters import join_filter
import config

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
    "set_limit_all_send_volume": set_limit_all_send_volume,
    "set_limit_send_id": set_limit_send_id,
    "change_donation_link": change_donation_link,
    "set_support_group": set_support_group_send_id,
    "set_max_users": set_max_users_send_value,
    "set_max_active_users": set_max_active_users_send_value,
    # s3
    "set_s3_access_key": set_s3_access_key,
    "set_s3_secret_key": set_s3_secret_key,
    "set_s3_endpoint": set_s3_endpoint,
}


@Client.on_message(
    filters.private
    & ~filters.command("start")
    & ~filters.command("help")
    & join_filter
)
async def handle_input(client: Client, message: Message) -> None:
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
        await send_message_send_message(message, user_id)
        return

    if SET_LIMIT_RE.match(state):
        await set_limit_set_limit(message, user_id)
        return


async def _support_group_filter(_, __, message: Message) -> bool:
    if not config.SUPPORT_GROUP or not message.reply_to_message:
        return False
    try:
        return message.chat.id == int(config.SUPPORT_GROUP)
    except (TypeError, ValueError):
        return False


support_group_filter = filters.create(_support_group_filter)


@Client.on_message(filters.group & support_group_filter)
async def handle_support_group_reply(client: Client, message: Message) -> None:
    await handle_support_reply(message)
