from pyrogram import Client
from pyrogram.types import CallbackQuery
from db.model_acync import is_user_exist, check_ban
from handlers.handler_helpers.callback_helper import back, set_bale_id, management, back_to_management, get_db, send_support_message, start, ban_bale, unban_bale, ban_telegram, unban_telegram
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