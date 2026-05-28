from pyrogram import Client
from pyrogram.types import CallbackQuery
from db.model_async import is_user_exist, check_ban
from handlers.handler_helpers.callback_helper import back, set_bale_id, management, back_to_management, get_db, send_support_message, start, ban_bale, unban_bale, ban_telegram, unban_telegram, show_10_high, set_join_ads, delete_join_ads, send_ads_message, send_message, add_admin, delete_admin, set_profile_photo, set_limit_all, set_limit, show_support_messages, help
from utils.filters import join_filter_cb



@Client.on_callback_query(join_filter_cb)
async def callback_handler(client: Client, callback: CallbackQuery):
    user_id = int(callback.from_user.id)
    is_exist = await is_user_exist(user_id)
    is_banned = await check_ban(user_id)


    #if user has banned
    if is_banned:
        return

    if callback.data == 'start':
        await start(callback.message, user_id)
        await callback.answer()
        return
    
    #if user not exist
    if is_exist == False:
        await callback.answer("کاربر یافت نشد", show_alert=True)
        return


    #/start
    if callback.data == 'set_bale_id':
        await set_bale_id(callback.message, user_id)
        await callback.answer()
        return

    if callback.data == 'send_support_message':
        await send_support_message(callback.message, user_id)
        await callback.answer()
        return


    if callback.data == 'help':
        await help(callback.message, user_id)
        await callback.answer()
        return
    
    if callback.data == 'management':
        await management(callback.message, user_id)
        await callback.answer()
        return
    

    #back
    if callback.data == 'back':
        await back(callback.message, user_id)
        await callback.answer()
        return

    #back to management
    if callback.data == 'back_to_management':
        await back_to_management(callback.message, user_id)
        await callback.answer()
        return


    if callback.data == 'get_db':
        await get_db(callback.message, user_id)
        await callback.answer()
        return
    
    if callback.data == 'ban_bale_id':
        await ban_bale(callback.message, user_id)
        await callback.answer()
        return

    if callback.data == 'unban_bale_id':
        await unban_bale(callback.message, user_id)
        await callback.answer()
        return
    
    if callback.data == 'ban_telegram_id':
        await ban_telegram(callback.message, user_id)
        await callback.answer()
        return
    
    if callback.data == 'unban_telegram_id':
        await unban_telegram(callback.message, user_id)
        await callback.answer()
        return
    
    if callback.data == 'show_10_high':
        await show_10_high(callback.message, user_id)
        await callback.answer()
        return
    
    if callback.data == 'set_join_ads':
        await set_join_ads(callback.message, user_id)
        await callback.answer()
        return
    
    if callback.data == 'delete_join_ads':
        await delete_join_ads(callback.message, user_id)
        await callback.answer()
        return
    
    if callback.data == 'send_ads':
        await send_ads_message(callback.message, user_id)
        await callback.answer()
        return
    
    if callback.data == 'send_message':
        await send_message(callback.message, user_id)
        await callback.answer()
        return
    
    if callback.data == 'add_admin':
        await add_admin(callback.message, user_id)
        await callback.answer()
        return
    
    if callback.data == 'delete_admin':
        await delete_admin(callback.message, user_id)
        await callback.answer()
        return
    
    if callback.data == 'set_profile_photo':
        await set_profile_photo(callback.message, user_id)
        await callback.answer()
        return
    
    
    if callback.data == 'set_limit_all':
        await set_limit_all(callback.message, user_id)
        await callback.answer()
        return
    
    if callback.data == 'set_limit':
        await set_limit(callback.message, user_id)
        await callback.answer()
        return

    if callback.data == 'show_support_messages':
        await show_support_messages(callback.message, user_id)
        await callback.answer()
        return