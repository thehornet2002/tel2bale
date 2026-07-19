"""
هندلر مربوط به تغییر عکس پروفایل ربات.
"""
import os
from pyrogram.types import Message
from db import model_async
from utils.keyboards import build_back_management_keyboard
from handlers.handler_helpers.message_helpers.common import admin_only


@admin_only
async def set_profile_photo_send_photo(message: Message, user_id: int):
    if not message.photo:
        await message.reply_text('پیامی که فرستادید حاوی عکس نمی باشد. لطفا دوباره تلاش کنید', reply_markup=build_back_management_keyboard())
        await model_async.set_state(user_id, 'management')
        return

    path = None
    try:
        path = await message.download()
        async for photo in message._client.get_chat_photos("me"):
            await message._client.delete_profile_photos(photo.file_id)

        await message._client.set_profile_photo(photo=path)
        await message.reply("✅ عکس پروفایل با موفقیت تغییر کرد!", reply_markup=build_back_management_keyboard())
        await model_async.set_state(user_id, 'management')
    except Exception as e:
        await message.reply(f"❌ خطا: {e}", reply_markup=build_back_management_keyboard())
        await model_async.set_state(user_id, 'management')
    finally:
        if path and os.path.exists(path):
            os.remove(path)