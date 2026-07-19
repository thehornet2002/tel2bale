"""
منطق اصلی فوروارد پیام‌ها از تلگرام به بله (شامل آپلود فایل‌های حجیم روی S3).
"""
import os
from pyrogram.types import Message
from db import model_async
from services.bale_service import bale_bot
from services import s3_service
from services.quota_service import check_and_update_quota, rollback_quota
from utils.keyboards import build_back_keyboard
from config import MAX_FILE_SIZE, IN_MEMORY
from utils.logger import get_logger

logger = get_logger(__name__)


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


async def forward(message: Message, user_id: int):
    bale_id = await model_async.get_bale_id(user_id)
    if not bale_id:
        await model_async.set_state(user_id, state='home')
        return await message.reply_text('خطا: شناسه بله شما یافت نشد.', reply_markup=build_back_keyboard())

    bot_token = await model_async.get_bale_token(user_id)
    if not bot_token:
        await model_async.set_state(user_id, state='home')
        return await message.reply_text(
            'لطفا توکن ربات را وارد کنید.',
            reply_markup=build_back_keyboard()
        )

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

    has_quota = await check_and_update_quota(user_id, file_size)
    if not has_quota:
        return await message.reply_text('حجم مجاز شما به اتمام رسیده است.')

    # 2.5 Large File → Upload to S3 and send link
    if file_size > MAX_FILE_SIZE:
        file_path = None
        try:
            access_key = await model_async.get_access_key(user_id)
            if not access_key:
                await model_async.set_state(user_id, state='home')
                return await message.reply_text(
                    'لطفا در ابتدا S3 را تنظیم کنید.',
                    reply_markup=build_back_keyboard()
                )

            secret_key = await model_async.get_secret_key(user_id)
            if not secret_key:
                await model_async.set_state(user_id, state='home')
                return await message.reply_text(
                    'لطفا در ابتدا S3 را تنظیم کنید.',
                    reply_markup=build_back_keyboard()
                )

            s3_endpoint = await model_async.get_s3_endpoint(user_id)
            if not s3_endpoint:
                await model_async.set_state(user_id, state='home')
                return await message.reply_text(
                    'لطفا در ابتدا S3 را تنظیم کنید.',
                    reply_markup=build_back_keyboard()
                )

            s3_connection = await s3_service.create_connection(access_key, secret_key)

            # FIX 1: ذخیره پیام وضعیت برای ویرایش بعدی
            status_msg = await message.reply_text('درحال دانلود ...')
            file_path = await message.download(in_memory=False)
            object_name = os.path.basename(file_path)

            await status_msg.edit_text('درحال آپلود ...')
            link = await s3_service.upload_file(
                session=s3_connection,
                file_path=file_path,
                endpoint_url=s3_endpoint,
                object_key=object_name
            )
            if not isinstance(link, str) or not link.startswith(("http://", "https://")):
                raise RuntimeError(link)
            result_msg = 'لینک موقت (یک ساعته) :' + '\n' + link
            await bale_bot.send_message(bot_token, bale_id, result_msg)
            await status_msg.edit_text(result_msg)

            if message.caption:
                await bale_bot.send_message(bot_token, bale_id, message.caption)

            return  # ← موفقیت‌آمیز، از تابع خارج می‌شیم

        except Exception as e:
            await rollback_quota(user_id, file_size)
            await message.reply_text(f"❌ خطا در فرآیند آپلود: {e}")
            return  # FIX 2: جلوگیری از Fallthrough به بخش ۳

        finally:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Cleanup: Temporary file {file_path} deleted.")
                except Exception as cleanup_error:
                    logger.error(f"Cleanup Error: Could not delete {file_path}. {cleanup_error}")

    # 3. Download and Forward Media
    file = None
    try:
        # FIX 1: ذخیره پیام وضعیت برای ویرایش بعدی
        status_msg = await message.reply_text('درحال دانلود ...')
        file = await message.download(in_memory=IN_MEMORY)
        if file and IN_MEMORY:
            file.seek(0)

        await status_msg.edit_text('درحال ارسال به بله ...')
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
            await status_msg.edit_text('توجه: ویدئوی گرد به صورت ویدئوی معمولی ارسال شد.')
            return
        else:
            return await status_msg.edit_text('این نوع پیام پشتیبانی نمی‌شود.')

        await status_msg.edit_text('پیام با موفقیت ارسال شد.')

    except Exception as e:
        await rollback_quota(user_id, file_size)
        await message.reply_text(text=format_bale_error(e), reply_markup=build_back_keyboard())

    finally:
        if isinstance(file, str) and os.path.exists(file):
            try:
                os.remove(file)
                logger.info(f"Cleanup: Temporary file {file} deleted.")
            except Exception as cleanup_error:
                logger.error(f"Cleanup Error: Could not delete {file}. {cleanup_error}")