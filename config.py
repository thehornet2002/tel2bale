import os
import asyncio
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

# Lock برای جلوگیری از race conditions
_env_lock = asyncio.Lock()


def _parse_list(value: str, cast_func=str):
    if not value:
        return []
    return [
        cast_func(item.strip())
        for item in value.split(",")
        if item.strip()
    ]


def _safe_int(value: str, default: int = 0) -> int:
    """جلوگیری از Crash در صورت None یا خالی بودن مقادیر ورودی"""
    try:
        return int(value) if value else default
    except (TypeError, ValueError):
        return default


# Telegram Config (حل مشکل Crash روی Import با مقادیر پیش‌فرض امن)
TEL_API_ID = _safe_int(os.getenv("TEL_API_ID"))
TEL_API_HASH = os.getenv("TEL_API_HASH", "")
TEL_BOT_TOKEN = os.getenv("TEL_BOT_TOKEN", "")

ADMIN_IDS = _parse_list(os.getenv("TEL_ADMIN_IDS", ""), int)

MAX_FILE_SIZE = _safe_int(os.getenv("TEL_MAX_FILE_SIZE"), 20) * 1024 * 1024

START_TXT = os.getenv("TEL_START_TXT", "")
HELP_TXT = os.getenv("TEL_HELP_TXT", "")
DONATION_LINK = os.getenv("DONATION_LINK","")
IN_MEMORY = os.getenv("TEL_IN_MEMORY", "False").lower() == "true"

ADS_CHANNELS = _parse_list(os.getenv("TEL_ADS_CHANNELS", ""))

# Telegram Proxy Config
_tel_proxy_scheme = os.getenv("TEL_PROXY_SCHEME")
_tel_proxy_host = os.getenv("TEL_PROXY_HOST")
_tel_proxy_port = os.getenv("TEL_PROXY_PORT")

TELPROXY = (
    dict(
        scheme=_tel_proxy_scheme,
        hostname=_tel_proxy_host,
        port=_safe_int(_tel_proxy_port)
    )
    if _tel_proxy_scheme and _tel_proxy_host and _tel_proxy_port
    else None
)


def _update_env_keys(updates: dict):
    """
    آپدیت هوشمند فایل .env:
    جایگزینی فقط کلیدهای تغییر یافته، حفظ کامنت‌ها و سایر متغیرها
    این تابع همگام (sync) است اما چون عملیات سریع I/O است مانعی ندارد.
    """
    env_path = ".env"
    lines = []
    
    # خواندن خطوط قبلی در صورت وجود فایل
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_lines = []
    updated_keys = set()

    for line in lines:
        stripped_line = line.strip()
        # نادیده گرفتن خطوط خالی و کامنت‌ها برای پارس کردن
        if stripped_line and not stripped_line.startswith("#"):
            parts = line.split("=", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                if key in updates:
                    # جایگزینی با مقدار جدید
                    new_lines.append(f"{key}={updates[key]}\n")
                    updated_keys.add(key)
                    continue
        
        # حفظ خطوط تغییر نیافته (کامنت‌ها، متغیرهای دیگر و...)
        new_lines.append(line)

    # اضافه کردن کلیدهای جدیدی که در فایل از قبل وجود نداشتند
    for key, val in updates.items():
        if key not in updated_keys:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines[-1] += "\n"
            new_lines.append(f"{key}={val}\n")

    # نوشتن مجدد بدون از دست دادن اطلاعات قبلی
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

async def update_donation_link(new_link: str):
    """
    تغییر لینک حمایت مالی:
    - اعتبارسنجی لینک
    - آپدیت مقدار داخل حافظه برنامه
    - ذخیره دائمی در فایل .env
    - rollback در صورت خطا
    """
    global DONATION_LINK

    async with _env_lock:
        old_link = DONATION_LINK
        DONATION_LINK = new_link

        try:
            # ذخیره دائمی در فایل .env
            _update_env_keys({
                "DONATION_LINK": DONATION_LINK
            })

            logger.info("[CONFIG] لینک حمایت مالی در فایل .env ذخیره شد.")
            return True

        except Exception as e:
            # rollback مقدار حافظه در صورت خطای ذخیره فایل
            DONATION_LINK = old_link
            logger.error(f"[CONFIG] خطا در ذخیره لینک حمایت مالی: {e}")
            return False

async def add_ads_channel(channel_id: str):
    """افزودن کانال جدید با حفظ ثبات داده و جلوگیری از Race Condition"""
    async with _env_lock:
        if channel_id in ADS_CHANNELS:
            return False

        ADS_CHANNELS.append(channel_id)
        
        try:
            _update_env_keys({"TEL_ADS_CHANNELS": ",".join(ADS_CHANNELS)})
            logger.info(f"[CONFIG] کانال {channel_id} اضافه شد.")
            return True
        except Exception as e:
            # Rollback: در صورت خطا در فایل، لیست حافظه به حالت قبل برمی‌گردد
            ADS_CHANNELS.remove(channel_id)
            logger.error(f"[CONFIG] خطا در اضافه کردن کانال (Rollback انجام شد): {e}")
            return False


async def remove_ads_channel(channel_id: str):
    """حذف کانال با حفظ ثبات داده و جلوگیری از Race Condition"""
    async with _env_lock:
        if channel_id not in ADS_CHANNELS:
            return False

        ADS_CHANNELS.remove(channel_id)
        
        try:
            _update_env_keys({"TEL_ADS_CHANNELS": ",".join(ADS_CHANNELS)})
            logger.info(f"[CONFIG] کانال {channel_id} حذف شد.")
            return True
        except Exception as e:
            # Rollback
            ADS_CHANNELS.append(channel_id)
            logger.error(f"[CONFIG] خطا در حذف کانال (Rollback انجام شد): {e}")
            return False


async def add_admin(admin_id: int):
    """افزودن ادمین جدید با حفظ ثبات داده و جلوگیری از Race Condition"""
    async with _env_lock:
        if admin_id in ADMIN_IDS:
            return False

        ADMIN_IDS.append(admin_id)
        
        try:
            _update_env_keys({"TEL_ADMIN_IDS": ",".join(map(str, ADMIN_IDS))})
            logger.info(f"[CONFIG] ادمین {admin_id} اضافه شد.")
            return True
        except Exception as e:
            # Rollback
            ADMIN_IDS.remove(admin_id)
            logger.error(f"[CONFIG] خطا در اضافه کردن ادمین (Rollback انجام شد): {e}")
            return False


async def remove_admin(admin_id: int):
    """حذف ادمین با حفظ ثبات داده و جلوگیری از Race Condition"""
    async with _env_lock:
        if admin_id not in ADMIN_IDS:
            return False

        ADMIN_IDS.remove(admin_id)
        
        try:
            _update_env_keys({"TEL_ADMIN_IDS": ",".join(map(str, ADMIN_IDS))})
            logger.info(f"[CONFIG] ادمین {admin_id} حذف شد.")
            return True
        except Exception as e:
            # Rollback
            ADMIN_IDS.append(admin_id)
            logger.error(f"[CONFIG] خطا در حذف ادمین (Rollback انجام شد): {e}")
            return False