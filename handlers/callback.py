from pyrogram import Client
from pyrogram.types import CallbackQuery
from db.model_acync import is_user_exist, check_ban
from handlers.handler_helpers.callback_helper import back, set_bale_id, management, back_to_management, get_db, send_support_message

@Client.on_callback_query()
async def callback_handler(client: Client, callback: CallbackQuery):
    user_id = int(callback.from_user.id)
    is_exist = await is_user_exist(user_id)
    is_banned = await check_ban(user_id)

    #if user has banned
    if is_banned:
        return

    #if user not exist
    if is_exist == False:
        await callback.answer("کاربر یافت نشد", show_alert=True)
        return

    if callback.data == 'set_bale_id':
        await set_bale_id(callback.message, user_id)
        return

    if callback.data == 'send_support_message':
        await send_support_message(callback.message, user_id)
        return


    if callback.data == 'help':
        await help(callback.message, user_id)
        return
    
    if callback.data == 'management':
        await management(callback.message, user_id)
        return
    

    #back
    if callback.data == 'back':
        await back(callback.message, user_id)
        return


    if callback.data == 'back_to_management':
        await back_to_management(callback.message, user_id)
        return

    if callback.data == 'get_user_json':
        await get_db(callback.message, user_id)
        return
    

    # if callback.data == 'ban_bale_id':
    #     if user_id == ADMIN_ID:
    #         user['user_step'] = 'enter_ban_bale_id'
    #         await callback.message.edit_text(
    #             'لطفا ID عدد کسی را که می خواهید Ban کنید وارد کنید.'
    #         )