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


# Telegram Config
TEL_API_ID = int(os.getenv("TEL_API_ID"))
TEL_API_HASH = os.getenv("TEL_API_HASH")
TEL_BOT_TOKEN = os.getenv("TEL_BOT_TOKEN")

ADMIN_IDS = _parse_list(os.getenv("TEL_ADMIN_IDS"), int)

MAX_FILE_SIZE = int(os.getenv("TEL_MAX_FILE_SIZE", 20)) * 1024 * 1024

START_TXT = os.getenv("TEL_START_TXT", "")
HELP_TXT = os.getenv("TEL_HELP_TXT", "")

IN_MEMORY = os.getenv("TEL_IN_MEMORY", "False").lower() == "true"

ADS_CHANNELS = _parse_list(os.getenv("TEL_ADS_CHANNELS"))


# Telegram Proxy Config
_tel_proxy_scheme = os.getenv("TEL_PROXY_SCHEME")
_tel_proxy_host = os.getenv("TEL_PROXY_HOST")
_tel_proxy_port = os.getenv("TEL_PROXY_PORT")

TELPROXY = (
    dict(
        scheme=_tel_proxy_scheme,
        hostname=_tel_proxy_host,
        port=int(_tel_proxy_port)
    )
    if _tel_proxy_scheme and _tel_proxy_host and _tel_proxy_port
    else None
)


async def _save_env():
    """ذخیره مقادیر فعلی در فایل .env"""
    async with _env_lock:
        env_data = {
            "TEL_API_ID": str(TEL_API_ID),
            "TEL_API_HASH": TEL_API_HASH,
            "TEL_BOT_TOKEN": TEL_BOT_TOKEN,

            "TEL_ADMIN_IDS": ",".join(map(str, ADMIN_IDS)),
            "TEL_START_TXT": START_TXT,
            "TEL_HELP_TXT": HELP_TXT,
            "TEL_ADS_CHANNELS": ",".join(ADS_CHANNELS),

            "TEL_MAX_FILE_SIZE": str(MAX_FILE_SIZE // (1024 * 1024)),
            "TEL_IN_MEMORY": str(IN_MEMORY),

            "TEL_PROXY_SCHEME": _tel_proxy_scheme or "",
            "TEL_PROXY_HOST": _tel_proxy_host or "",
            "TEL_PROXY_PORT": str(_tel_proxy_port or ""),
        }

        try:
            with open(".env", "w", encoding="utf-8") as f:
                for key, value in env_data.items():
                    f.write(f"{key}={value}\n")
            logger.info("[CONFIG] فایل .env با موفقیت ذخیره شد.")
        except Exception as e:
            logger.error(f"[CONFIG] خطا در ذخیره فایل .env: {e}")
            raise


async def add_ads_channel(channel_id: str):
    """افزودن کانال جدید به لیست ADS_CHANNELS و ذخیره در .env"""
    if channel_id in ADS_CHANNELS:
        return False

    ADS_CHANNELS.append(channel_id)
    await _save_env()
    logger.info(f"[CONFIG] کانال {channel_id} اضافه شد.")
    return True


async def remove_ads_channel(channel_id: str):
    """حذف کانال از لیست ADS_CHANNELS و ذخیره در .env"""
    if channel_id not in ADS_CHANNELS:
        return False

    ADS_CHANNELS.remove(channel_id)
    await _save_env()
    logger.info(f"[CONFIG] کانال {channel_id} حذف شد.")
    return True


async def add_admin(admin_id: int):
    """افزودن ادمین جدید به لیست ADMIN_IDS و ذخیره در .env"""
    if admin_id in ADMIN_IDS:
        return False

    ADMIN_IDS.append(admin_id)
    await _save_env()
    logger.info(f"[CONFIG] ادمین {admin_id} اضافه شد.")
    return True


async def remove_admin(admin_id: int):
    """حذف ادمین از لیست ADMIN_IDS و ذخیره در .env"""
    if admin_id not in ADMIN_IDS:
        return False

    ADMIN_IDS.remove(admin_id)
    await _save_env()
    logger.info(f"[CONFIG] ادمین {admin_id} حذف شد.")
    return True
