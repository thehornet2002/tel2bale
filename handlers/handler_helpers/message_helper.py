import re
import os
import asyncio
from functools import wraps
from pyrogram.types import Message
from db import model_async
from services.bale_service import bale_bot
from utils.keyboards import build_back_keyboard, build_back_management_keyboard
from config import add_ads_channel, remove_ads_channel, add_admin, remove_admin, MAX_FILE_SIZE, IN_MEMORY, update_donation_link
from services.quota_service import check_and_update_quota
from services import s3_service
from utils.logger import get_logger
from urllib.parse import urlparse
from pyrogram.errors import ChannelInvalid, ChannelPrivate, PeerIdInvalid, UsernameInvalid, UsernameNotOccupied
from utils.parser import validate_link
from services.quota_service import rollback_quota
logger = get_logger(__name__)

# ==========================================
# Helpers & Decorators
# ==========================================
def normalize_telegram_channel_input(raw_value: str) -> str | int | None:
    value = (raw_value or "").strip()

    if not value:
        return None

    value = value.split()[0]

    if value.startswith("http://") or value.startswith("https://"):
        parsed = urlparse(value)
        host = parsed.netloc.lower()
        path = parsed.path.strip("/")

        if host not in ("t.me", "telegram.me", "www.t.me", "www.telegram.me"):
            return None

        if not path:
            return None

        if path.startswith("+") or path.startswith("joinchat/"):
            return None

        value = path.split("/")[0]

    elif value.startswith("t.me/") or value.startswith("telegram.me/"):
        value = value.split("/", 1)[1].strip("/").split("/")[0]

    value = value.strip()

    if value.startswith("@"):
        value = value[1:]

    if re.fullmatch(r"-?\d+", value):
        return int(value)

    if not re.fullmatch(r"[A-Za-z0-9_]{5,32}", value):
        return None

    return f"@{value}"


def ads_channel_aliases(raw_value: str, normalized_value: str | int | None = None) -> set[str]:
    aliases: set[str] = set()

    if raw_value:
        raw = raw_value.strip()
        aliases.add(raw)
        aliases.add(raw.lstrip("@"))

    if normalized_value is not None:
        aliases.add(str(normalized_value))
        if isinstance(normalized_value, str):
            aliases.add(normalized_value.lstrip("@"))

    return {item for item in aliases if item}


async def resolve_and_validate_ads_channel(message: Message, raw_value: str) -> tuple[str | None, str | None]:
    normalized = normalize_telegram_channel_input(raw_value)

    if normalized is None:
        return None, (
            "فرمت کانال معتبر نیست.\n\n"
            "فرمت‌های قابل قبول:\n"
            "@channel\n"
            "channel\n"
            "https://t.me/channel\n"
            "-1001234567890"
        )

    try:
        chat = await message._client.get_chat(normalized)
    except (UsernameInvalid, UsernameNotOccupied, PeerIdInvalid, ChannelInvalid):
        return None, "کانالی با این مشخصات پیدا نشد."
    except ChannelPrivate:
        return None, (
            "کانال خصوصی است یا ربات به آن دسترسی ندارد.\n"
            "ابتدا ربات را عضو کانال کنید، سپس دوباره تلاش کنید."
        )
    except Exception as e:
        return None, f"خطا در بررسی کانال:\n{e}"

    chat_id = chat.id

    try:
        member = await message._client.get_chat_member(chat_id, "me")
    except Exception:
        return None, (
            "ربات در این کانال عضو نیست یا دسترسی بررسی عضویت ندارد.\n"
            "ابتدا ربات را به کانال اضافه کنید."
        )

    status_value = getattr(member.status, "value", str(member.status))

    if status_value not in ("creator", "administrator", "member", "owner"):
        return None, "ربات در این کانال عضو نیست."

    if getattr(chat, "username", None):
        return f"@{chat.username}", None

    return str(chat_id), None
    
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
    await model_async.set_state(user_id,'home')
    await message.reply_text('ID عددی شما در بله با موفقیت ثبت شد.', reply_markup=build_back_keyboard())

async def set_s3_access_key(message: Message, user_id: int):
    await model_async.set_access_key(user_id, message.text)
    await model_async.set_state(user_id, 'set_s3_secret_key')
    await message.reply_text('لطفا Secret Key را وارد نمایید.', reply_markup=build_back_keyboard())

async def set_s3_secret_key(message: Message, user_id: int):
    await model_async.set_secret_key(user_id, message.text)
    await model_async.set_state(user_id, 'set_s3_endpoint')
    await message.reply_text(
        'لطفا S3 EndPoint را به صورت لینک وارد کنید.',
        reply_markup=build_back_keyboard()
    )

async def set_s3_endpoint(message:Message, user_id:int):
    endpoint_url = await validate_link(message.text)
    if not endpoint_url:
        await message.reply_text('لطفا Endpoint را به صورت لینک وارد کنید.', reply_markup=build_back_keyboard())
        return
    access_key = await model_async.get_access_key(user_id)
    secret_key = await model_async.get_secret_key(user_id)
    valid_s3 = await s3_service.verify_credentials(access_key=access_key, secret_key=secret_key, endpoint_url=endpoint_url)
    if not valid_s3:
        await model_async.set_access_key(user_id, None)
        await model_async.set_secret_key(user_id, None)
        await model_async.set_state(user_id, 'home')
        await message.reply_text(
            'لطفا مشخصات S3 معتبر وارد کنید',
            reply_markup=build_back_keyboard()
        )
        return
    await model_async.set_s3_endpoint(user_id, endpoint_url)
    await model_async.set_state(user_id, 'home')
    await message.reply_text(
        'اطلاعات S3 با موفقیت ذخیره شد.',
        reply_markup=build_back_keyboard()
    )

async def set_bale_token_bot(message: Message, user_id: int):
    verify_state = await bale_bot.verify_token(message.text)
    if verify_state:
        await model_async.set_bale_token(user_id, message.text)
        await model_async.set_state(user_id, 'home')
        await message.reply_text('توکن ربات بله با موفقیت ثبت شد.', reply_markup=build_back_keyboard())
    else:
        await model_async.set_state(user_id,'home')
        await message.reply_text(
            'توکن بات بله معتبر نمی باشد لطفا دوباره تلاش کنید.',
            reply_markup=build_back_keyboard()
        )

async def send_support_message(message: Message, user_id: int):
    await model_async.save_support_message(user_id, message_text=str(message.text))
    await model_async.set_state(user_id, 'home')
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
    channel_value, error = await resolve_and_validate_ads_channel(message, message.text or "")
    if error:
        await message.reply_text(error, reply_markup=build_back_management_keyboard())
        return

    if not await add_ads_channel(channel_value):
        await message.reply_text('این کانال قبلاً در لیست Join اجباری ثبت شده است.', reply_markup=build_back_management_keyboard())
        return

    await model_async.set_state(user_id, 'management')
    await message.reply_text(
        f'کانال با موفقیت اضافه شد.\nشناسه ذخیره‌شده: {channel_value}',
        reply_markup=build_back_management_keyboard()
    )

@admin_only
async def enter_delete_join_ads(message: Message, user_id: int):
    channel_value, _ = await resolve_and_validate_ads_channel(message, message.text or "")

    removed = False
    for alias in ads_channel_aliases(message.text or "", channel_value):
        if await remove_ads_channel(alias):
            removed = True
            break

    if not removed:
        await message.reply_text('این کانال در لیست Join اجباری پیدا نشد.', reply_markup=build_back_management_keyboard())
        return

    await model_async.set_state(user_id, 'management')
    await message.reply_text('کانال با موفقیت حذف شد.', reply_markup=build_back_management_keyboard())

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
            await model_async.set_state('home')
    except Exception:
        await message.reply_text("❌ خطا در ارسال پیام", reply_markup=build_back_management_keyboard())
        await model_async.set_state('home')

@admin_only
async def add_admin_send_id(message: Message, user_id: int):
    target_id = await get_valid_id(message)
    if not target_id:
        await model_async.set_state('management')
        return
        
    if not await model_async.set_admin(target_id):
        await message.reply_text('مشکل در تغییر در دیتابیس', reply_markup=build_back_management_keyboard())
        await model_async.set_state('management')
        return
        
    if not await add_admin(target_id):
        await message.reply_text('مشکل در فایل .env', reply_markup=build_back_management_keyboard())
        await model_async.set_state('management')
        return
    
    await message.reply_text('کاربر مورد نظر ادمین شد.', reply_markup=build_back_management_keyboard())
    await model_async.set_state('management')

@admin_only
async def delete_admin_send_id(message: Message, user_id: int):
    target_id = await get_valid_id(message)
    if not target_id:
        await model_async.set_state('management')
        return

    if not await remove_admin(target_id):
        await message.reply_text('مشکل در فایل .env', reply_markup=build_back_management_keyboard())
        await model_async.set_state('management')
        return
        
    if not await model_async.unset_admin(target_id):
        await message.reply_text('مشکل در تغییر در دیتابیس', reply_markup=build_back_management_keyboard())
        await model_async.set_state('management')
        return

    await message.reply_text('فرد مورد نظر از ادمینی خارج شد.', reply_markup=build_back_management_keyboard())
    await model_async.set_state('management')

@admin_only
async def set_profile_photo_send_photo(message: Message, user_id: int):
    if not message.photo:
        await message.reply_text('پیامی که فرستادید حاوی عکس نمی باشد. لطفا دوباره تلاش کنید', reply_markup=build_back_management_keyboard())
        await model_async.set_state('management')
        return

    path = None
    try:
        path = await message.download()
        async for photo in message._client.get_chat_photos("me"):
            await message._client.delete_profile_photos(photo.file_id)

        await message._client.set_profile_photo(photo=path)
        await message.reply("✅ عکس پروفایل با موفقیت تغییر کرد!", reply_markup=build_back_management_keyboard())
        await model_async.set_state('management')
    except Exception as e:
        await message.reply(f"❌ خطا: {e}", reply_markup=build_back_management_keyboard())
        await model_async.set_state('management')
    finally:
        if path and os.path.exists(path):
            os.remove(path)

@admin_only
async def set_limit_all_send_volume(message: Message, user_id: int):
    try:
        value = float(message.text)
        await model_async.set_limit_download_all(value)
        await model_async.set_limit_volume(value)
        await model_async.set_state(user_id ,state='management')
        await message.reply_text('محدودیت با موفقیت اعمال شد.', reply_markup=build_back_management_keyboard())
        await model_async.set_state('management')
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
            await model_async.set_state(user_id ,state='management')
            await message.reply_text('محدودیت با موفقیت اعمال شد.', reply_markup=build_back_management_keyboard())
    except Exception:
        await model_async.set_state(user_id ,state='management')
        await message.reply_text("❌ خطا در اعمال محدودیت", reply_markup=build_back_management_keyboard())

@admin_only
async def change_donation_link(message:Message, user_id:int):
    try:
        new_link = await validate_link(message.text)
        if not new_link:
            await model_async.set_state(user_id, state='management')
            await message.reply_text(
                'لطفا لینک معتبر وارد کنید.',
                reply_markup=build_back_management_keyboard()
            )
            return
        result = await update_donation_link(new_link)
        if not result:
            await model_async.set_state(user_id, state='management')
            await message.reply_text(
                'لطفا لینک معتبر وارد کنید.',
                reply_markup=build_back_management_keyboard()
            )
            return
        await model_async.set_state(user_id, state='management')
        await message.reply_text(
            'لینک دونیت با موفقیت تغییر کرد.',
            reply_markup=build_back_management_keyboard()
        )
        await model_async.set_state('management')
    except Exception:
            await model_async.set_state(user_id, state='management')
            await message.reply_text(
                'تغییر لینک دونیت با مشکل مواجه شد.',
                reply_markup=build_back_management_keyboard()
            )
            await model_async.set_state('management')

# ==========================================
# Core Forward Logic
# ==========================================

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