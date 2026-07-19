"""
هندلرهای مربوط به تنظیم محدودیت حجم دانلود کاربران.
"""
import re
from pyrogram.types import Message
from db import model_async
from utils.keyboards import build_back_management_keyboard
from handlers.handler_helpers.message_helpers.common import admin_only, get_valid_id


@admin_only
async def set_limit_all_send_volume(message: Message, user_id: int):
    try:
        value = float(message.text)
    except ValueError:
        await message.reply_text('لطفا فقط عدد ارسال کنید.')
        return

    await model_async.set_limit_download_all(value)
    await model_async.set_limit_volume(value)
    await model_async.set_state(user_id, 'management')
    await message.reply_text('محدودیت با موفقیت اعمال شد.', reply_markup=build_back_management_keyboard())


@admin_only
async def set_limit_send_id(message: Message, user_id: int):
    target_id = await get_valid_id(message)
    if not target_id:
        return

    if not await model_async.is_user_exist(target_id):
        await model_async.set_state(user_id, 'management')
        await message.reply_text('کاربری با این ID عددی در دیتابیس یافت نشد.', reply_markup=build_back_management_keyboard())
        return

    await model_async.set_state(user_id, f'set_limit_{target_id}')
    await message.reply_text('لطفا میزان محدودیتی که می خواهید اعمال کنید را وارد کنید (به GB):', reply_markup=build_back_management_keyboard())


@admin_only
async def set_limit_set_limit(message: Message, user_id: int):
    try:
        limit_value = float(message.text)
    except ValueError:
        await message.reply_text('لطفا فقط عدد (حجم به گیگابایت) ارسال کنید.')
        return

    state = await model_async.get_state(user_id)
    try:
        m = re.match(r"^set_limit_(\d+)$", state)
        if not m:
            await model_async.set_state(user_id, 'management')
            await message.reply_text("❌ خطا در اعمال محدودیت", reply_markup=build_back_management_keyboard())
            return

        target_id = int(m.group(1))

        if not await model_async.is_user_exist(target_id):
            await model_async.set_state(user_id, 'management')
            await message.reply_text('کاربری با این ID عددی در دیتابیس یافت نشد.', reply_markup=build_back_management_keyboard())
            return

        await model_async.set_limit_download(target_id, limit_value)
        await model_async.set_state(user_id, 'management')
        await message.reply_text('محدودیت با موفقیت اعمال شد.', reply_markup=build_back_management_keyboard())
    except Exception:
        await model_async.set_state(user_id, 'management')
        await message.reply_text("❌ خطا در اعمال محدودیت", reply_markup=build_back_management_keyboard())
