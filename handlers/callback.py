from pyrogram import Client
from pyrogram.types import CallbackQuery

from db.model_async import (
    check_ban,
    is_user_exist,
)

from handlers.handler_helpers.callback_helper import (
    add_admin,
    back,
    back_to_management,
    ban_bale,
    ban_telegram,
    delete_admin,
    delete_join_ads,
    get_db,
    help,
    management,
    send_ads_message,
    send_message,
    send_support_message,
    set_bale_id,
    set_join_ads,
    set_limit,
    set_limit_all,
    set_profile_photo,
    show_10_high,
    show_support_messages,
    start,
    unban_bale,
    unban_telegram,
    reset_bale_id,
    set_s3,
    reset_s3_access_key,
    set_bale_bot_token,
    reset_bot_token,
    change_donation_link,
)

from utils.filters import join_filter_cb


CALLBACK_ROUTES = {
    #main page
    "start": start,
    #set
    "set_bale_id": set_bale_id,
    "set_bale_bot_token":set_bale_bot_token,
    "set_s3":set_s3,
    "reset_s3_access_key": reset_s3_access_key,
    #resets
    "reset_bale_id": reset_bale_id,
    "reset_bot_token": reset_bot_token,
    #other
    "send_support_message": send_support_message,
    "help": help,
    "management": management,
    
    #backs
    "back": back,
    "back_to_management": back_to_management,
    
    #managemet
    "get_db": get_db,
    "ban_bale_id": ban_bale,
    "unban_bale_id": unban_bale,
    "ban_telegram_id": ban_telegram,
    "unban_telegram_id": unban_telegram,
    "show_10_high": show_10_high,
    "set_join_ads": set_join_ads,
    "delete_join_ads": delete_join_ads,
    "send_ads": send_ads_message,
    "send_message": send_message,
    "add_admin": add_admin,
    "delete_admin": delete_admin,
    "set_profile_photo": set_profile_photo,
    "set_limit_all": set_limit_all,
    "set_limit": set_limit,
    "show_support_messages": show_support_messages,
    "change_donation_link": change_donation_link,
}


@Client.on_callback_query(join_filter_cb)
async def callback_handler(
    client: Client,
    callback: CallbackQuery
) -> None:

    user_id = callback.from_user.id

    if await check_ban(user_id):
        await callback.answer()
        return

    if callback.data != "start":
        if not await is_user_exist(user_id):
            await callback.answer(
                "کاربر یافت نشد",
                show_alert=True
            )
            return

    handler = CALLBACK_ROUTES.get(callback.data)

    if handler is None:
        await callback.answer()
        return

    await handler(
        callback.message,
        user_id
    )

    await callback.answer()