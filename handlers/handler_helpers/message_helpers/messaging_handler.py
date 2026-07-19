"""
هندلرهای مربوط به ارسال پیام: پیام همگانی (broadcast) و پیام مستقیم به یک کاربر.
"""
import re
import asyncio
from pyrogram.types import Message
from db import model_async
from utils.keyboards import build_back_keyboard, build_back_management_keyboard
from handlers.handler_helpers.message_helpers.common import admin_only, get_valid_id


@admin_only
async def enter_ads_message(message: Message, user_id: int):
    tg_ids = await model_async.get_all_telegram_ids()
    success, failed = 0, 0

    for tg_id in tg_ids:
        try:
            if await model_async.check_admin(tg_id):
                continue
            await message.copy(chat_id=tg_id)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await message.reply_text(f"✅ ارسال تمام شد\n\nموفق: {success}\nناموفق: {failed}", reply_markup=build_back_keyboard())
    await model_async.set_state(user_id, 'home')


@admin_only
async def send_message_chat_id(message: Message, user_id: int):
    target_id = await get_valid_id(message)
    if not target_id:
        return

    await model_async.set_state(user_id, f'send_message_{target_id}')
    await message.reply_text('لطفا پیام خود را ارسال کنید.', reply_markup=build_back_management_keyboard())


@admin_only
async def send_message_send_message(message: Message, user_id: int):
    state = await model_async.get_state(user_id)
    try:
        if m := re.match(r"^send_message_(\d+)$", state):
            target_id = int(m.group(1))
            await message.copy(chat_id=target_id)
            await message.reply_text("✅ پیام با موفقیت ارسال شد", reply_markup=build_back_management_keyboard())
        await model_async.set_state(user_id, 'home')
    except Exception:
        await message.reply_text("❌ خطا در ارسال پیام (احتمالا کاربر ربات را بلاک کرده است)", reply_markup=build_back_management_keyboard())
        await model_async.set_state(user_id, 'home')