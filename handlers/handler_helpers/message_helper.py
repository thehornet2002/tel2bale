import re
import os
import asyncio
from functools import wraps
from pyrogram.types import Message
from db import model_async
from utils.code_generator import generate_random_code
from services.bale_service import bale_bot
from utils.keyboards import build_start_keyboard, build_back_keyboard, build_back_management_keyboard
from config import add_ads_channel, remove_ads_channel, add_admin, remove_admin, MAX_FILE_SIZE, IN_MEMORY
from services.quota_service import check_and_update_quota


# ==========================================
# Helpers & Decorators
# ==========================================

def admin_only(func):
    """دکوریتور برای بررسی اینکه آیا کاربر ادمین هست یا خیر."""
    @wraps(func)
    async def wrapper(message: Message, user_id: int, *args, **kwargs):
        is_admin = await model_async.check_admin(user_id)
        if not is_admin:
            return  # ادمین نیست، هیچ کاری نکن (یا پیام خطای دسترسی بده)
        return await func(message, user_id, *args, **kwargs)
    return wrapper

async def get_valid_id(message: Message) -> int | None:
    """بررسی می‌کند که متن پیام حتما یک عدد باشد و آن را برمی‌گرداند."""
    if not message.text or not message.text.isdigit():
        await message.reply_text("لطفا فقط شناسه عددی ارسال کنید.")
        return None
    return int(message.text)

def format_bale_error(error: Exception) -> str:
    """فرمت کردن خطاهای دریافتی از بله (نیازی به async ندارد)"""
    text = str(error).lower()
    
    if "unauthorized" in text:
        return "❌ توکن ربات بله نامعتبر است.\nلطفاً توکن را مجدداً بررسی کنید."
    if "chat not found" in text:
        return "❌ شناسه بله معتبر نیست یا ربات به آن دسترسی ندارد."
    if "forbidden" in text:
        return "❌ ربات بله اجازه ارسال پیام به این کاربر را ندارد."
    if "connection" in text:
        return "❌ ارتباط با سرورهای بله برقرار نشد.\nلطفاً کمی بعد دوباره تلاش کنید."
        
    return f"❌ خطا در ارسال:\n{str(error)}"


# ==========================================
# User Handlers
# ==========================================

async def enter_bale_id(message: Message, user_id: int):
    id_num = await get_valid_id(message)
    if not id_num: return

    await model_async.set_bale_id(tg_id=user_id, bale_id=id_num)
    await message.reply_text('ID عددی شما در بله با موفقیت ثبت شد.', reply_markup=build_back_keyboard())

async def set_access_key(message: Message, user_id: int):
    await model_async.set_access_key(user_id, message.text)
    await model_async.set_state(user_id, 'set_secret_key_arvan')
    await message.reply_text('لطفا Secret Key را وارد نمایید.', reply_markup=build_back_keyboard())

async def set_secret_key(message: Message, user_id: int):
    await model_async.set_secret_key(user_id, message.text)
    await model_async.set_state(user_id, 'home')
    await message.reply_text('Secret Key و Access Key با موفقیت ثبت شدند.', reply_markup=build_back_keyboard())

async def set_bale_token_bot(message: Message, user_id: int):
    await model_async.set_bale_token(user_id, message.text)
    await message.reply_text('توکن ربات بله با موفقیت ثبت شد.', reply_markup=build_back_keyboard())

async def send_support_message(message: Message, user_id: int):
    await model_async.save_support_message(user_id, message_text=str(message.text))
    await message.reply_text('پیام شما با موفقیت ارسال شد', reply_markup=build_back_keyboard())


# ==========================================
# Admin Handlers
# ==========================================

@admin_only
async def enter_bale_ban(message: Message, user_id: int):
    bale_id = await get_valid_id(message)
    if not bale_id: return

    tg_ids = await model_async.get_telegram_ids_by_bale_id(bale_id=bale_id)
    for i in tg_ids:
        await model_async.ban_user(i)
    await message.reply_text('کاربر با خاک یکسان شد.', reply_markup=build_back_management_keyboard())

@admin_only
async def enter_bale_unban(message: Message, user_id: int):
    bale_id = await get_valid_id(message)
    if not bale_id: return

    tg_ids = await model_async.get_telegram_ids_by_bale_id(bale_id)
    for i in tg_ids:
        await model_async.unban_user(i)
    await message.reply_text('کاربر از بن خارج شد', reply_markup=build_back_management_keyboard())

@admin_only
async def enter_telegram_ban(message: Message, user_id: int):
    tg_id = await get_valid_id(message)
    if not tg_id: return

    await model_async.ban_user(tg_id)
    await message.reply_text('کاربر با خاک یکسان شد.', reply_markup=build_back_management_keyboard())

@admin_only
async def enter_telegram_unban(message: Message, user_id: int):
    tg_id = await get_valid_id(message)
    if not tg_id: return

    await model_async.unban_user(tg_id)
    await message.reply_text('کاربر از بن خارج شد.', reply_markup=build_back_management_keyboard())

@admin_only
async def enter_join_ads_channel(message: Message, user_id: int):
    await add_ads_channel(message.text)
    await message.reply_text('کانال با موفقیت اضافه شد.', reply_markup=build_back_management_keyboard())

@admin_only
async def enter_delete_join_ads(message: Message, user_id: int):
    await remove_ads_channel(message.text)
    await message.reply_text('کانال با موفقیت حذف شد', reply_markup=build_back_management_keyboard())

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
    
    await message.reply_text(f"✅ ارسال تمام شد\n\nموفق: {success}\nناموفق: {failed}")
    await model_async.set_state(user_id, 'home')

@admin_only
async def send_message_chat_id(message: Message, user_id: int):
    target_id = await get_valid_id(message)
    if not target_id: return

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
    except Exception:
        await message.reply_text("❌ خطا در ارسال پیام", reply_markup=build_back_management_keyboard())

@admin_only
async def add_admin_send_id(message: Message, user_id: int):
    target_id = await get_valid_id(message)
    if not target_id: return

    if not await add_admin(target_id):
        await message.reply_text('مشکل در فایل config.json', reply_markup=build_back_management_keyboard())
        return
        
    if not await model_async.set_admin(target_id):
        await message.reply_text('مشکل در تغییر در دیتابیس', reply_markup=build_back_management_keyboard())
        return
        
    await message.reply_text('کاربر مورد نظر ادمین شد.', reply_markup=build_back_management_keyboard())

@admin_only
async def delete_admin_send_id(message: Message, user_id: int):
    target_id = await get_valid_id(message)
    if not target_id: return

    if not await remove_admin(target_id):
        await message.reply_text('مشکل در فایل config.json', reply_markup=build_back_management_keyboard())
        
    if not await model_async.unset_admin(target_id):
        await message.reply_text('مشکل در تغییر در دیتابیس', reply_markup=build_back_management_keyboard())
        
    await message.reply_text('فرد مورد نظر از ادمینی خارج شد.', reply_markup=build_back_management_keyboard())

@admin_only
async def set_profile_photo_send_photo(message: Message, user_id: int):
    if not message.photo:
        await message.reply_text('پیامی که فرستادید حاوی عکس نمی باشد. لطفا دوباره تلاش کنید', reply_markup=build_back_management_keyboard())
        return

    path = None
    try:
        path = await message.download()
        async for photo in message._client.get_chat_photos("me"):
            await message._client.delete_profile_photos(photo.file_id)

        await message._client.set_profile_photo(photo=path)
        await message.reply("✅ عکس پروفایل با موفقیت تغییر کرد!", reply_markup=build_back_management_keyboard())
    except Exception as e:
        await message.reply(f"❌ خطا: {e}", reply_markup=build_back_management_keyboard())
    finally:
        if path and os.path.exists(path):
            os.remove(path)

@admin_only
async def set_limit_all_send_volume(message: Message, user_id: int):
    try:
        value = float(message.text)
        await model_async.set_limit_download_all(value)
        await message.reply_text('محدودیت با موفقیت اعمال شد.', reply_markup=build_back_management_keyboard())
    except ValueError:
        await message.reply_text('لطفا فقط عدد ارسال کنید.')

@admin_only
async def set_limit_send_id(message: Message, user_id: int):
    target_id = await get_valid_id(message)
    if not target_id: return

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
        if m := re.match(r"^set_limit_(\d+)$", state):
            target_id = int(m.group(1))
            await model_async.set_limit_download(target_id, limit_value)
            await message.reply_text('محدودیت با موفقیت اعمال شد.', reply_markup=build_back_management_keyboard())
    except Exception:
        await message.reply_text("❌ خطا در اعمال محدودیت", reply_markup=build_back_management_keyboard())


# ==========================================
# Core Forward Logic
# ==========================================

async def forward(message: Message, user_id: int):
    bale_id = await model_async.get_bale_id(user_id)
    if not bale_id:
        return await message.reply_text('خطا: شناسه بله شما یافت نشد.', reply_markup=build_back_keyboard())

    bot_token = await model_async.get_bale_token(user_id)

    # 1. Handle Non-Media Messages First
    try:
        if message.text:
            await bale_bot.send_message(bot_token, bale_id, message.text)
            return await message.reply_text('پیام با موفقیت ارسال شد.')
            
        if message.location:
            await bale_bot.send_location(bot_token, bale_id, message.location.latitude, message.location.longitude)
            return await message.reply_text('موقعیت مکانی با موفقیت ارسال شد.')
            
        if message.contact:
            await bale_bot.send_contact(bot_token, bale_id, message.contact.phone_number, message.contact.first_name, message.contact.last_name or "")
            return await message.reply_text('شماره تماس با موفقیت ارسال شد.')
            
    except Exception as e:
        return await message.reply_text(format_bale_error(e))

    # 2. Check Media Limitations
    if message.sticker:
        return await message.reply_text('این سرویس از سمت بله برای ربات‌ها بسته شده است.')

    media_obj = getattr(message, message.media.value) if message.media else None
    if not media_obj:
        return await message.reply_text('این نوع پیام پشتیبانی نمی‌شود.')

    file_size = getattr(media_obj, 'file_size', 0)

    if file_size > MAX_FILE_SIZE:
        return await message.reply_text('حجم فایل بیشتر از محدودیت مجاز است.')

    has_quota = await check_and_update_quota(user_id, file_size)
    if not has_quota:
        return await message.reply_text('حجم مجاز شما به اتمام رسیده است.')

    # 3. Download and Forward Media
    try:
        file = await message.download(in_memory=IN_MEMORY)
        if file:
            file.seek(0)

        caption = message.caption or ""

        if message.photo:
            await bale_bot.send_photo(bot_token, bale_id, file, caption)
        elif message.video:
            await bale_bot.send_video(bot_token, bale_id, file, caption)
        elif message.audio:
            await bale_bot.send_audio(bot_token, bale_id, file, caption)
        elif message.voice:
            await bale_bot.send_voice(bot_token, bale_id, file, caption)
        elif message.document:
            await bale_bot.send_document(bot_token, bale_id, file, message.document.file_name, caption)
        elif message.animation:
            await bale_bot.send_animation(bot_token, bale_id, file, caption)
        elif message.video_note:
            await bale_bot.send_video(bot_token, bale_id, file)
            await message.reply_text('توجه: ویدئوی گرد به صورت ویدئوی معمولی ارسال شد.')
        else:
            return await message.reply_text('این نوع پیام پشتیبانی نمی‌شود.')

        await message.reply_text('پیام با موفقیت ارسال شد.')

    except Exception as e:
        await message.reply_text(text=format_bale_error(e), reply_markup=build_back_keyboard())