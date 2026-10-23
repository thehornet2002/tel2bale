"""
Handlers for multimedia downloads (YouTube, Instagram, Spotify, etc.)
and cookie / quota management.
"""
import os
import time
import uuid
from pyrogram.types import CallbackQuery, Message
import config
from db import model_async
from services import downloader_service, s3_service
from services.bale_service import bale_bot
from services.cookie_service import (
    delete_cookie_file,
    get_cookie_status,
    save_cookie_file,
)
from services.quota_service import get_quota_details, reserve_download_quota
from utils.keyboards import (
    build_admin_cookie_keyboard,
    build_back_keyboard,
    build_back_management_keyboard,
    build_cancel_reply_keyboard,
    build_media_quality_keyboard,
    build_user_cookie_keyboard,
)
from utils.logger import get_logger

logger = get_logger(__name__)

# Temporary store for pending download requests
_PENDING_DOWNLOADS: dict[str, dict] = {}


def _clean_expired_downloads() -> None:
    now = time.time()
    expired = [k for k, v in _PENDING_DOWNLOADS.items() if now - v.get("created_at", 0) > 1800]
    for k in expired:
        _PENDING_DOWNLOADS.pop(k, None)


async def handle_media_link_request(message: Message, user_id: int, raw_url: str) -> bool:
    """
    Process recognized media URL (YouTube, Instagram, Spotify, etc.),
    fetch available formats, and present interactive quality selection keyboard.
    """
    url = downloader_service.extract_media_url(raw_url) or raw_url.strip()
    status_msg = await message.reply_text("🔍 در حال بررسی لینک و دریافت اطلاعات رسانه...")

    try:
        info = await downloader_service.get_media_info(url, user_id=user_id)
    except Exception as e:
        logger.warning(f"[MEDIA] Extraction failed for {url}: {e}")
        await status_msg.edit_text(
            f"⚠️ امکان استخراج مستقیم از این لینک وجود نداشت: {e}\nدر حال ارسال به عنوان متن ساده به بله..."
        )
        return False

    _clean_expired_downloads()
    token = uuid.uuid4().hex[:10]
    _PENDING_DOWNLOADS[token] = {
        "user_id": user_id,
        "url": url,
        "platform": info["platform"],
        "title": info["title"],
        "duration": info["duration"],
        "thumbnail": info["thumbnail"],
        "spotify_query": info.get("spotify_query"),
        "created_at": time.time(),
    }

    platform_names = {
        "youtube": "یوتیوب (YouTube)",
        "instagram": "اینستاگرام (Instagram)",
        "spotify": "اسپاتیفای (Spotify)",
        "generic": "وب‌سایت چندرسانه‌ای",
    }
    platform_label = platform_names.get(info["platform"], info["platform"])

    duration_str = ""
    if info.get("duration"):
        mins = info["duration"] // 60
        secs = info["duration"] % 60
        duration_str = f"\n⏱ مدت زمان: **{mins:02d}:{secs:02d}**"

    caption = (
        f"🎬 **{info['title']}**\n"
        f"🌐 پلتفرم: **{platform_label}**"
        f"{duration_str}\n\n"
        "کیفیت مورد نظر خود را جهت دانلود و ارسال به بله انتخاب فرمایید:"
    )

    kb = build_media_quality_keyboard(token, info["platform"], info["qualities"])
    try:
        await status_msg.delete()
    except Exception:
        pass

    await message.reply_text(caption, reply_markup=kb)
    return True


async def execute_media_download(callback: CallbackQuery, user_id: int, token: str, quality: str) -> None:
    """Download selected format, check quota, and forward media to Bale."""
    data = _PENDING_DOWNLOADS.get(token)
    if not data:
        await callback.answer("درخواست منقضی شده است. لطفاً مجدداً لینک را ارسال فرمایید.", show_alert=True)
        return

    if data["user_id"] != user_id:
        await callback.answer("این درخواست متعلق به حساب شما نیست.", show_alert=True)
        return

    bale_id = await model_async.get_bale_id(user_id)
    bot_token = await model_async.get_bale_token(user_id)
    if not bale_id or not bot_token:
        await callback.answer("ابتدا باید شناسه بله و توکن ربات بله خود را تنظیم کنید.", show_alert=True)
        return

    # Check remaining quota before downloading
    quota_info = await get_quota_details(user_id)
    if not quota_info["is_unlimited"] and quota_info["remaining_mb"] <= 1.0:
        await callback.answer("سقف حجم دانلود شما به اتمام رسیده است.", show_alert=True)
        return

    await callback.answer()
    status_text = f"⏳ در حال دانلود رسانه با کیفیت {quality}... لطفاً شکیبا باشید."
    try:
        await callback.message.edit_text(status_text)
    except Exception:
        pass

    try:
        file_path, title, file_size = await downloader_service.download_media(
            url=data["url"],
            quality=quality,
            user_id=user_id,
            is_spotify=(data["platform"] == "spotify"),
            spotify_query=data.get("spotify_query"),
        )
    except Exception as e:
        logger.error(f"[DOWNLOADER] Download execution failed: {e}")
        try:
            await callback.message.edit_text(
                f"❌ خطا در دانلود رسانه:\n{e}",
                reply_markup=build_back_keyboard()
            )
        except Exception:
            pass
        return

    file_size_mb = file_size / (1024 * 1024)
    file_size_gb = file_size / (1024 ** 3)

    # Atomic quota reservation
    has_quota = await reserve_download_quota(user_id, file_size)
    if not has_quota:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        try:
            await callback.message.edit_text(
                f"❌ حجم فایل دانلودشده ({file_size_mb:.1f} MB) از سقف مجاز باقیمانده شما بیشتر است.\nارسال به بله لغو شد.",
                reply_markup=build_back_keyboard()
            )
        except Exception:
            pass
        return

    try:
        await callback.message.edit_text(
            f"⏳ دانلود کامل شد ({file_size_mb:.1f} MB).\nدر حال آماده‌سازی و ارسال به پیام‌رسان بله..."
        )
    except Exception:
        pass

    # Send to Bale
    try:
        if file_size <= config.MAX_FILE_SIZE:
            ext = os.path.splitext(file_path)[1].lower()
            if ext in (".mp3", ".m4a", ".ogg", ".wav", ".aac") or quality in ("audio", "320k", "192k", "128k"):
                await bale_bot.send_audio(bot_token, bale_id, file_path, caption=title[:255])
            elif ext in (".mp4", ".mkv", ".mov", ".webm"):
                await bale_bot.send_video(bot_token, bale_id, file_path, caption=title[:255])
            else:
                await bale_bot.send_document(
                    bot_token,
                    bale_id,
                    file_path,
                    filename=os.path.basename(file_path),
                    caption=title[:255]
                )
        else:
            # Upload to S3 if larger than MAX_FILE_SIZE
            access_key = await model_async.get_access_key(user_id)
            secret_key = await model_async.get_secret_key(user_id)
            endpoint = await model_async.get_s3_endpoint(user_id)
            if not access_key or not secret_key or not endpoint:
                raise RuntimeError(
                    f"حجم فایل ({file_size_mb:.1f} MB) از سقف ارسال مستقیم بزرگتر است و فضای S3 تنظیم نشده است."
                )

            s3_conn = await s3_service.create_connection(access_key, secret_key)
            link = await s3_service.upload_file(
                session=s3_conn,
                file_path=file_path,
                endpoint_url=endpoint,
                object_key=os.path.basename(file_path),
            )
            if not isinstance(link, str) or not link.startswith(("http://", "https://")):
                raise RuntimeError(link)

            bale_caption = f"🎬 {title}\n📦 حجم: {file_size_mb:.1f} MB\n🔗 لینک دانلود مستقیم (یک ساعته):\n{link}"
            await bale_bot.send_message(bot_token, bale_id, bale_caption)

    except Exception as e:
        logger.error(f"[MEDIA] Forwarding downloaded media to Bale failed: {e}")
        try:
            await callback.message.edit_text(
                f"❌ خطا در ارسال فایل به بله:\n{e}",
                reply_markup=build_back_keyboard()
            )
        except Exception:
            pass
        return
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        _PENDING_DOWNLOADS.pop(token, None)

    updated_quota = await get_quota_details(user_id)
    remaining_txt = "نامحدود ♾" if updated_quota["is_unlimited"] else f"{updated_quota['remaining_mb']:.1f} MB"

    success_text = (
        "✅ **فایل با موفقیت دانلود و به بله ارسال شد!**\n\n"
        f"🎬 عنوان: **{title}**\n"
        f"📦 حجم مصرف‌شده: **{file_size_mb:.2f} مگابایت**\n"
        f"📊 سهمیه باقیمانده شما: **{remaining_txt}**"
    )
    try:
        await callback.message.edit_text(success_text, reply_markup=build_back_keyboard())
    except Exception:
        pass


async def execute_send_as_text(callback: CallbackQuery, user_id: int, token: str) -> None:
    """Forward original URL text directly to Bale without downloading."""
    data = _PENDING_DOWNLOADS.pop(token, None)
    if not data:
        await callback.answer("درخواست منقضی شده است.", show_alert=True)
        return

    bale_id = await model_async.get_bale_id(user_id)
    bot_token = await model_async.get_bale_token(user_id)
    if not bale_id or not bot_token:
        await callback.answer("شناسه بله یا توکن ربات بله شما تنظیم نشده است.", show_alert=True)
        return

    await callback.answer()
    try:
        await bale_bot.send_message(bot_token, bale_id, data["url"])
        await callback.message.edit_text(
            f"✅ لینک زیر به عنوان پیام متنی به بله ارسال شد:\n`{data['url']}`",
            reply_markup=build_back_keyboard()
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ خطا در ارسال پیام به بله: {e}",
            reply_markup=build_back_keyboard()
        )


async def execute_cancel_download(callback: CallbackQuery, token: str) -> None:
    """Cancel pending media download request."""
    _PENDING_DOWNLOADS.pop(token, None)
    await callback.answer("دانلود لغو شد.")
    try:
        await callback.message.delete()
    except Exception:
        pass


# ==========================================
# Cookie Handlers (Admin & User)
# ==========================================

async def admin_manage_cookies(message: Message, user_id: int) -> None:
    """Display admin global cookie configuration panel."""
    status = get_cookie_status()
    if status["has_cookie"]:
        size_kb = status["size_bytes"] / 1024
        text = (
            "🍪 **مدیریت کوکی‌های عمومی (Global Cookies)**\n\n"
            f"وضعیت: 🟢 **فعال**\n"
            f"حجم فایل: **{size_kb:.2f} کیلوبایت**\n"
            f"مسیر ذخیره: `{status['path']}`\n\n"
            "این کوکی‌ها برای کلیه دانلودهای یوتیوب و اینستاگرام اعمال می‌شوند."
        )
    else:
        text = (
            "🍪 **مدیریت کوکی‌های عمومی (Global Cookies)**\n\n"
            "وضعیت: ⚪️ **تنظیم نشده**\n\n"
            "با تنظیم کوکی عمومی، یوتیوب و اینستاگرام محدودیت‌های سنی و خطاهای احراز هویت را رفع می‌کنند."
        )

    kb = build_admin_cookie_keyboard(status["has_cookie"])
    await message.reply_text(text, reply_markup=kb)


async def admin_save_cookies_message(message: Message, user_id: int) -> None:
    """Save admin uploaded cookies.txt."""
    content = ""
    if message.document:
        dl_path = await message.download(in_memory=False)
        try:
            with open(dl_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        finally:
            if os.path.exists(dl_path):
                os.remove(dl_path)
    elif message.text:
        content = message.text

    if not content or len(content.strip()) < 10:
        await message.reply_text(
            "❌ محتوای کوکی نامعتبر است. لطفاً فایل معتبر cookies.txt را ارسال کنید.",
            reply_markup=build_back_management_keyboard()
        )
        return

    success = save_cookie_file(content, user_id=None)
    await model_async.set_state(user_id, "management")
    if success:
        await message.reply_text(
            "✅ کوکی عمومی با موفقیت ذخیره و فعال شد.",
            reply_markup=build_back_management_keyboard()
        )
    else:
        await message.reply_text(
            "❌ خطا در ذخیره‌سازی فایل کوکی.",
            reply_markup=build_back_management_keyboard()
        )


async def user_cookie_menu(message: Message, user_id: int) -> None:
    """Display user custom cookie panel."""
    status = get_cookie_status(user_id)
    if status["is_user_specific"] and status["has_cookie"]:
        size_kb = status["size_bytes"] / 1024
        text = (
            "🍪 **تنظیمات کوکی اختصاصی شما**\n\n"
            f"وضعیت: 🟢 **فعال (کوکی اختصاصی شما)**\n"
            f"حجم فایل: **{size_kb:.2f} KB**\n\n"
            "در صورت دانلود، ابتدا کوکی اختصاصی شما اولویت خواهد داشت."
        )
    elif status["has_cookie"]:
        text = (
            "🍪 **تنظیمات کوکی**\n\n"
            "وضعیت: 🟢 **کوکی عمومی سرور فعال است**\n"
            "(می‌توانید در صورت تمایل کوکی اختصاصی خود را نیز اضافه فرمایید)."
        )
    else:
        text = (
            "🍪 **تنظیمات کوکی اختصاصی**\n\n"
            "وضعیت: ⚪️ **کوکی تنظیم نشده است**\n"
            "افزودن کوکی برای رفع محدودیت‌ها یا دانلود از اکانت شخصی اختیاری است."
        )

    kb = build_user_cookie_keyboard(status["is_user_specific"] and status["has_cookie"])
    if getattr(message, "outgoing", False) or getattr(getattr(message, "from_user", None), "is_self", False):
        try:
            await message.edit_text(text, reply_markup=kb)
            return
        except Exception:
            pass
    await message.reply_text(text, reply_markup=kb)


async def user_save_cookies_message(message: Message, user_id: int) -> None:
    """Save user uploaded cookies.txt."""
    content = ""
    if message.document:
        dl_path = await message.download(in_memory=False)
        try:
            with open(dl_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        finally:
            if os.path.exists(dl_path):
                os.remove(dl_path)
    elif message.text:
        content = message.text

    if not content or len(content.strip()) < 10:
        await message.reply_text(
            "❌ محتوای کوکی نامعتبر است. لطفاً فایل معتبر cookies.txt ارسال کنید.",
            reply_markup=build_back_keyboard()
        )
        return

    success = save_cookie_file(content, user_id=user_id)
    await model_async.set_state(user_id, "home")
    if success:
        await message.reply_text(
            "✅ کوکی اختصاصی شما با موفقیت ذخیره شد.",
            reply_markup=build_back_keyboard()
        )
    else:
        await message.reply_text(
            "❌ خطا در ذخیره کوکی اختصاصی.",
            reply_markup=build_back_keyboard()
        )


async def show_user_quota_info(message: Message, user_id: int) -> None:
    """Show detailed user download quota breakdown."""
    info = await get_quota_details(user_id)
    unlimited_str = "نامحدود ♾"
    limit_txt = unlimited_str if info["is_unlimited"] else f"**{info['limit_gb']:.2f} گیگابایت** ({info['limit_gb'] * 1024:.0f} MB)"
    remaining_txt = unlimited_str if info["is_unlimited"] else f"**{info['remaining_mb']:.1f} مگابایت** ({info['remaining_gb']:.3f} GB)"

    text = (
        "📊 **گزارش سهمیه و مصرف ترافیک شما:**\n\n"
        f"• حجم مصرف‌شده کل: **{info['downloaded_mb']:.2f} مگابایت** ({info['downloaded_gb']:.3f} GB)\n"
        f"• سقف مجاز دانلود: {limit_txt}\n"
        f"• سهمیه باقیمانده: {remaining_txt}\n\n"
        "💡 *ترافیک دانلود از یوتیوب، اینستاگرام، اسپاتیفای و فایل‌های ارسالی بر اساس این سهمیه محاسبه می‌گردد.*"
    )

    if getattr(message, "outgoing", False) or getattr(getattr(message, "from_user", None), "is_self", False):
        try:
            await message.edit_text(text, reply_markup=build_back_keyboard())
            return
        except Exception:
            pass
    await message.reply_text(text, reply_markup=build_back_keyboard())
