from pyrogram.types import Message
from db.model_async import get_send_attempts, get_cooldown, set_send_attempts, set_cooldown, set_verify_code, set_state, get_verify_code, set_verified, check_admin,save_support_message, get_telegram_ids_by_bale_id, ban_user, set_bale_id, unban_user, get_all_telegram_ids, get_state, set_admin, unset_admin, set_limit_download_all, set_limit_download, verify_check, get_bale_id, get_downloaded_volume,get_limit_download, set_downloaded_volume
from utils.code_generator import generate_random_code
from services.bale_service import send_verify_code, send_message, send_photo, send_video, send_audio, send_voice, send_document, send_animation, send_location, send_contact
from utils.keyboards import build_start_keyboard, build_back_keyboard, build_back_management_keyboard
from config import add_ads_channel, remove_ads_channel, add_admin, remove_admin, MAX_FILE_SIZE, IN_MEMORY
from services.quota_service import check_and_update_quota
import time
import re
import os
import asyncio


async def enter_bale_id(message:Message, user_id:int):
    if not message.text.isdigit():
            await message.reply_text("لطفا فقط شناسه عددی ارسال کنید.")
            return
    id_num = int(message.text)
    attempts = await get_send_attempts(user_id)
    now = int(time.time())
    cooldown = await get_cooldown(user_id)
    if attempts >= 3:
        #cooldown check
        if now >= int(cooldown) if cooldown else 0:
            await set_send_attempts(user_id,0)
        else:
            remaining = int(cooldown) - now
            message_txt = f'لطفا صبر کنید و {remaining} ثانیه دیگر دوباره تلاش کنید.'
            await message.reply_text(message_txt, reply_markup=build_back_keyboard())
    else:
        if attempts == 2:
            await set_cooldown(user_id,str(int(time.time())+900))
        await set_send_attempts(user_id,attempts+1)
        code = await generate_random_code()
        await set_verify_code(user_id,code,str(int(time.time())+120))
        await send_verify_code(id_num,str(code))
        await set_state(user_id, 'enter_verify_code')
        await set_bale_id(user_id,id_num)
        await message.reply_text(
             'کد احراز هویت برای اکانت بله شما ارسال شد. لطفا کد را وارد کنید',
             reply_markup=build_back_keyboard()
             )


async def enter_verify_code(message: Message, user_id:int):
    if not message.text.isdigit():
        await message.reply_text("لطفا فقط عدد وارد کنید.")
        return
    client_code = int(message.text)
    verify_code, verify_expire = await get_verify_code(user_id)
    if verify_expire and int(verify_expire) >= int(time.time()):
        if verify_code == client_code:
            await set_verified(user_id,True)
            await set_state(user_id,'home')
            await set_send_attempts(user_id,0)
            await set_verify_code(user_id,0,"")
            await set_cooldown(user_id,'')
            await message.reply_text(
                'احراز هویت شما با موفقیت انجام شد',
                reply_markup=build_start_keyboard(await check_admin(user_id))
            )
        else:
             await message.reply_text(
                'کد را اشتباه وارد کردید. لطفا دوباره کد را وارد کنید:',
                reply_markup=build_back_keyboard()
            )
    else:
        await message.reply_text(
            'زمان ارسال کد به پایان رسیده لطفا دوباره تلاش کنید',
            reply_markup=build_back_keyboard()
        )


async def send_support_message(message:Message, user_id:int):
        await save_support_message(user_id,message_text=str(message.text))
        await message.reply_text(
             'پیام شما با موفقیت ارسال شد',
             reply_markup=build_back_keyboard()
        )


async def enter_bale_ban(message:Message, user_id:int):
    is_admin = await check_admin(user_id)
    if is_admin :
        if not message.text.isdigit():
            await message.reply_text("لطفا فقط شناسه عددی ارسال کنید.")
            return
        bale_id = int(message.text)
        tg_ids = await get_telegram_ids_by_bale_id(bale_id=bale_id)
        for i in tg_ids:
            await ban_user(i)
        await message.reply_text(
            'کاربر با خاک یکسان شد.',
            reply_markup=build_back_management_keyboard()
        )


async def enter_bale_unban(message:Message, user_id:int):
    is_admin = await check_admin(user_id)
    if is_admin:
        if not message.text.isdigit():
            await message.reply_text("لطفا فقط شناسه عددی ارسال کنید.")
            return
        bale_id = int(message.text)
        tg_ids = await get_telegram_ids_by_bale_id(bale_id)
        for i in tg_ids:
            await unban_user(i)
        await message.reply_text(
             'کاربر از بن خارج شد',
             reply_markup=build_back_management_keyboard()
        )


async def enter_telegram_ban(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if is_admin:
        if not message.text.isdigit():
            await message.reply_text("لطفا فقط شناسه عددی ارسال کنید.")
            return
        tg_id = int(message.text)
        await ban_user(tg_id)
        await message.reply_text(
            'کاربر با خاک یکسان شد.',
            reply_markup=build_back_management_keyboard()
        )

async def enter_telegram_unban(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if is_admin:
        if not message.text.isdigit():
            await message.reply_text('لطفا فقط شناسه عددی ارسال کنید.')
            return
        tg_id = int(message.text)
        await unban_user(tg_id)
        await message.reply_text(
            'کاربر از بن خارج شد.',
            reply_markup=build_back_management_keyboard()
        )

async def enter_join_ads_channel(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if is_admin:
        await add_ads_channel(message.text)
        await message.reply_text(
            'کانال با موفقیت اضافه شد.',
            reply_markup=build_back_management_keyboard()
        )


async def enter_delete_join_ads(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if is_admin:
        await remove_ads_channel(message.text)
        await message.reply_text(
            'کانال با موفقیت حذف شد',
            reply_markup=build_back_management_keyboard()
        )

async def enter_ads_message(message: Message, user_id: int):
    is_admin = await check_admin(user_id)
    if not is_admin:
        return
    
    tg_ids = await get_all_telegram_ids()
    success = 0
    failed = 0
    
    for tg_id in tg_ids:
        try:
            if await check_admin(tg_id):
                continue
            await message.copy(chat_id=tg_id)
            success += 1
            await asyncio.sleep(0.05)  # جلوگیری از بلاک شدن توسط تلگرام
        except Exception:
            failed += 1
    
    await message.reply_text(
        f"✅ ارسال تمام شد\n\n"
        f"موفق: {success}\n"
        f"ناموفق: {failed}"
    )
    await set_state(user_id, 'home')


async def send_message_chat_id(message:Message, user_id:int):
    is_admin = await check_admin(user_id)
    if not is_admin:
        return
    if not message.text.isdigit():
            await message.reply_text('لطفا فقط شناسه عددی ارسال کنید.')
            return
    new_state = 'send_message_' + message.text
    await set_state(user_id , new_state)
    await message.reply_text(
        'لطفا پیام خود را ارسال کنید.',
        reply_markup=build_back_management_keyboard()
    )

async def send_message_send_message(message: Message, user_id: int):
    is_admin = await check_admin(user_id)
    if not is_admin:
        return
    
    state = await get_state(user_id)
    try:
        pattern = re.compile(r"^send_message_(\d+)$")
        m = pattern.match(state)
        if not m:
            return None
        
        target_id = int(m.group(1))
        await message.copy(chat_id=target_id)
        await message.reply_text(
            "✅ پیام با موفقیت ارسال شد",
            reply_markup=build_back_management_keyboard()
        )
    
    except Exception as e:
        await message.reply_text(
            "❌ خطا در ارسال پیام",
            reply_markup=build_back_management_keyboard()
        )


async def add_admin_send_id(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if not is_admin:
        return
    if not message.text.isdigit():
        await message.reply_text('لطفا فقط شناسه عددی ارسال کنید.')
        return
    add_admin_flag = await add_admin(int(message.text))
    if add_admin_flag == False:
        await message.reply_text(
            'مشکل در فایل config.json',
            reply_markup=build_back_management_keyboard()
        )
        return
    set_admin_flag = await set_admin(int(message.text))
    if set_admin_flag == False:
        await message.reply_text(
            'مشکل در تغییر در دیتابیس',
            reply_markup=build_back_management_keyboard()
        )
        return
    await message.reply_text(
        'کاربر مورد نظر ادمین شد.',
        reply_markup=build_back_management_keyboard()
    )


async def delete_admin_send_id(message:Message, user_id:int):
    is_admin = await check_admin(user_id)
    if not is_admin:
        return
    if not message.text.isdigit():
        await message.reply_text('لطفا فقط شناسه عددی ارسال کنید.')
        return
    flag_remove_admin = await remove_admin(int(message.text))
    if flag_remove_admin == False:
        await message.reply_text(
            'مشکل در فایل config.json',
            reply_markup=build_back_management_keyboard()
        )
    flag_unset_admin = await unset_admin(int(message.text))
    if flag_unset_admin == False:
        await message.reply_text(
            'مشکل در تغییر در دیتابیس',
            reply_markup=build_back_management_keyboard()
        )
    await message.reply_text(
        'فرد مورد نظر از ادمینی خارج شد.',
        reply_markup=build_back_management_keyboard()
    )


async def set_profile_photo_send_photo(message: Message, user_id: int):
    is_admin = await check_admin(user_id)
    if not is_admin:
        return

    if not message.photo:
        await message.reply_text(
            'پیامی که فرستادید حاوی عکس نمی باشد. لطفا دوباره تلاش کنید',
            reply_markup=build_back_management_keyboard()
        )
        return

    path = None
    try:
        path = await message.download()
        # ✅ از message.client استفاده می‌کنیم نه client
        async for photo in message._client.get_chat_photos("me"):
            await message._client.delete_profile_photos(photo.file_id)

        await message._client.set_profile_photo(photo=path)

        await message.reply(
            "✅ عکس پروفایل با موفقیت تغییر کرد!",
            reply_markup=build_back_management_keyboard()
        )
    except Exception as e:
        await message.reply(
            f"❌ خطا: {e}",
            reply_markup=build_back_management_keyboard()
        )
    finally:
        if path and os.path.exists(path):
            os.remove(path)


async def set_limit_all_send_volume(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if not is_admin:
        return
    try:
        value = float(message.text)
    except ValueError:
        await message.reply_text('لطفا فقط عدد ارسال کنید.')
        return
    
    await set_limit_download_all(float(message.text))
    await message.reply_text(
        'محدودیت با موفقیت اعمال شد.',
        reply_markup=build_back_management_keyboard()
    )


async def set_limit_send_id(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if not is_admin:
        return
    if not message.text.isdigit():
        await message.reply_text('لطفا فقط عدد ارسال کنید.')
        return
    state = 'set_limit_' + str(message.text)
    await set_state(user_id, state)
    await message.reply_text(
        'لطفا میزان محدودیتی که می خواهید اعمال کنید را وارد کنید (به GB):',
        reply_markup=build_back_management_keyboard()
    )


async def set_limit_set_limit(message: Message, user_id: int):
    is_admin = await check_admin(user_id)
    if not is_admin:
        return
        
    try:
        limit_value = float(message.text)
    except ValueError:
        await message.reply_text('لطفا فقط عدد (حجم به گیگابایت) ارسال کنید.')
        return

    state = await get_state(user_id)
    try:
        pattern = re.compile(r"^set_limit_(\d+)$")
        m = pattern.match(state)
        if not m:
            return None
        
        target_id = int(m.group(1))
        await set_limit_download(target_id, limit_value)
        await message.reply_text(
            'محدودیت با موفقیت اعمال شد.',
            reply_markup=build_back_management_keyboard()    
        )
    except Exception as e:
        await message.reply_text(
            "❌ خطا در اعمال محدودیت",
            reply_markup=build_back_management_keyboard()
        )



async def forward(message: Message, user_id: int):
    if not await verify_check(user_id):
        await message.reply_text(
            'شما احراز هویت در بله انجام نداده‌اید.',
            reply_markup=build_back_keyboard()
        )
        return

    bale_id = await get_bale_id(user_id)
    if not bale_id:
        await message.reply_text('خطا: شناسه بله شما یافت نشد.')
        return

    # 1. مدیریت پیام‌های متنی، لوکیشن و کانتکت (مواردی که نیاز به دانلود ندارند)
    if message.text:
        await send_message(bale_id, message.text)
        await message.reply_text('پیام با موفقیت ارسال شد.')
        return
        
    if message.location:
        await send_location(bale_id, message.location.latitude, message.location.longitude)
        await message.reply_text('موقعیت مکانی با موفقیت ارسال شد.')
        return
        
    if message.contact:
        last_name = message.contact.last_name or ""
        await send_contact(bale_id, message.contact.phone_number, message.contact.first_name, last_name)
        await message.reply_text('شماره تماس با موفقیت ارسال شد.')
        return

    # 2. مدیریت استیکر (عدم پشتیبانی بله)
    if message.sticker:
        await message.reply_text('این سرویس از سمت بله برای ربات‌ها بسته شده است.')
        return

    # 3. پیدا کردن آبجکت مدیا (عکس، ویدیو، داکیومنت و ...)
    media_obj = getattr(message, message.media.value) if message.media else None
    
    if not media_obj:
        await message.reply_text('این نوع پیام پشتیبانی نمی‌شود.')
        return

    # 4. بررسی محدودیت سایز فایل
    file_size = getattr(media_obj, 'file_size', 0)
    if file_size > MAX_FILE_SIZE:
        await message.reply_text('حجم فایل بیشتر از محدودیت مجاز است و قابل ارسال نیست.')
        return

    # 5. بررسی محدودیت حجم دانلود کاربر
    has_quota = await check_and_update_quota(user_id, file_size)
    if not has_quota:
        await message.reply_text('حجم مجاز شما به اتمام رسیده است.')
        return

    # 6. دانلود فایل در مموری (بدون تبدیل به بایت)
    file = await message.download(in_memory=IN_MEMORY)
    
    # برگرداندن نشانگر فایل به نقطه صفر بسیار مهم است، در غیر این صورت فایل خالی ارسال می‌شود
    if file:
        file.seek(0)
        
    caption = message.caption or ""

    # 7. مسیریابی و ارسال به سرویس بله بر اساس نوع مدیا (پاس دادن مستقیم file object)
    try:
        if message.photo:
            await send_photo(bale_id, file, caption)
        elif message.video:
            await send_video(bale_id, file, caption)
        elif message.audio:
            await send_audio(bale_id, file, caption)
        elif message.voice:
            await send_voice(bale_id, file, caption)
        elif message.document:
            await send_document(bale_id, file, message.document.file_name, caption)
        elif message.animation:
            await send_animation(bale_id, file, caption)
        elif message.video_note:
            await send_video(bale_id, file) 
            await message.reply_text('توجه: این پیام به صورت ویدئوی معمولی ارسال شد (بله از ویدئوی گرد پشتیبانی نمی‌کند).')
        else:
            await message.reply_text('این نوع پشتیبانی نمی‌شود.')
            return
            
        await message.reply_text('پیام با موفقیت ارسال شد.')

    except Exception:
        await message.reply_text('ارسال با خطا مواجه شد. لطفاً دوباره تلاش کنید.')