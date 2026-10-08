import os
import asyncio
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

# Mutex lock to prevent race conditions during environment updates
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
    """Safely cast string to integer with fallback default."""
    try:
        return int(value) if value else default
    except (TypeError, ValueError):
        return default


# Telegram Bot Configuration
TEL_API_ID = _safe_int(os.getenv("TEL_API_ID"))
TEL_API_HASH = os.getenv("TEL_API_HASH", "")
TEL_BOT_TOKEN = os.getenv("TEL_BOT_TOKEN", "")

ADMIN_IDS = _parse_list(os.getenv("TEL_ADMIN_IDS", ""), int)

MAX_FILE_SIZE = _safe_int(os.getenv("TEL_MAX_FILE_SIZE"), 20) * 1024 * 1024

START_TXT = os.getenv("TEL_START_TXT", "")
HELP_TXT = os.getenv("TEL_HELP_TXT", "")
DONATION_LINK = os.getenv("DONATION_LINK", "")
IN_MEMORY = os.getenv("TEL_IN_MEMORY", "False").lower() == "true"
SUPPORT_MESSAGE_LIMIT = _safe_int(os.getenv('SUPPORT_MESSAGE_LIMIT'), 5)

# Capacity Limits (0 = Unlimited)
MAX_USERS = _safe_int(os.getenv('MAX_USERS'), 0)
MAX_ACTIVE_USERS = _safe_int(os.getenv('MAX_ACTIVE_USERS'), 0)

ADS_CHANNELS = _parse_list(os.getenv("TEL_ADS_CHANNELS", ""))

WHITELIST_USERS = _parse_list(os.getenv("TEL_WHITELIST_USERS", ""), int)
WHITELIST_ENABLED = os.getenv("TEL_WHITELIST_ENABLED", "False").strip().lower() == "true"

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "").strip().strip('\'"') or None

# Proxy Helpers
def _clean_env(value: str | None) -> str:
    """Strip whitespace and quotation marks from environment values."""
    if value is None:
        return ""
    return value.strip().strip('\'"')


def _normalize_proxy_url(value: str | None, default_scheme: str = "http") -> str | None:
    """Normalize proxy string into standard URL format for aiohttp."""
    value = _clean_env(value)
    if not value:
        return None
    if "://" not in value:
        value = f"{default_scheme}://{value}"
    return value


# Telegram Proxy Configuration
_tel_proxy_scheme = _clean_env(os.getenv("TEL_PROXY_SCHEME"))
_tel_proxy_host = _clean_env(os.getenv("TEL_PROXY_HOST"))
_tel_proxy_port = _safe_int(os.getenv("TEL_PROXY_PORT"))

TELPROXY = (
    {
        "scheme": _tel_proxy_scheme,
        "hostname": _tel_proxy_host,
        "port": _tel_proxy_port,
    }
    if _tel_proxy_scheme and _tel_proxy_host and _tel_proxy_port
    else None
)

# Bale Proxy Configuration
BALE_PROXY = _clean_env(os.getenv("BALE_PROXY"))
BALE_PROXY_URL = _normalize_proxy_url(BALE_PROXY)


def _update_env_keys(updates: dict):
    """
    Update selected keys in .env file while preserving comments and existing variables.
    Sanitizes values against CRLF injection.
    """
    env_path = ".env"
    lines = []

    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_lines = []
    updated_keys = set()

    for line in lines:
        stripped_line = line.strip()
        if stripped_line and not stripped_line.startswith("#"):
            parts = line.split("=", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                if key in updates:
                    clean_val = str(updates[key]).replace("\r", "").replace("\n", "").strip()
                    new_lines.append(f"{key}={clean_val}\n")
                    updated_keys.add(key)
                    continue

        new_lines.append(line)

    for key, val in updates.items():
        clean_val = str(val).replace("\r", "").replace("\n", "").strip()
        if key not in updated_keys:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines[-1] += "\n"
            new_lines.append(f"{key}={clean_val}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


async def set_max_users(value: int) -> bool:
    """Set total registration user capacity (0 = unlimited)."""
    global MAX_USERS

    async with _env_lock:
        old_value = MAX_USERS
        MAX_USERS = value
        try:
            _update_env_keys({"MAX_USERS": str(value)})
            return True
        except Exception as e:
            MAX_USERS = old_value
            logger.error(f"[CONFIG] Error saving MAX_USERS: {e}")
            return False


async def set_max_active_users(value: int) -> bool:
    """Set maximum active users with configured Bale tokens (0 = unlimited)."""
    global MAX_ACTIVE_USERS

    async with _env_lock:
        old_value = MAX_ACTIVE_USERS
        MAX_ACTIVE_USERS = value
        try:
            _update_env_keys({"MAX_ACTIVE_USERS": str(value)})
            return True
        except Exception as e:
            MAX_ACTIVE_USERS = old_value
            logger.error(f"[CONFIG] Error saving MAX_ACTIVE_USERS: {e}")
            return False


async def update_donation_link(new_link: str):
    """Update donation link in memory and persist in .env file with rollback."""
    global DONATION_LINK

    async with _env_lock:
        old_link = DONATION_LINK
        DONATION_LINK = new_link

        try:
            _update_env_keys({"DONATION_LINK": DONATION_LINK})
            logger.info("[CONFIG] Donation link updated successfully.")
            return True
        except Exception as e:
            DONATION_LINK = old_link
            logger.error(f"[CONFIG] Error saving donation link: {e}")
            return False


async def add_ads_channel(channel_id: str):
    """Add mandatory join channel and persist to .env."""
    async with _env_lock:
        if channel_id in ADS_CHANNELS:
            return False

        ADS_CHANNELS.append(channel_id)

        try:
            _update_env_keys({"TEL_ADS_CHANNELS": ",".join(ADS_CHANNELS)})
            logger.info(f"[CONFIG] Added channel: {channel_id}")
            return True
        except Exception as e:
            ADS_CHANNELS.remove(channel_id)
            logger.error(f"[CONFIG] Error adding channel: {e}")
            return False


async def remove_ads_channel(channel_id: str):
    """Remove mandatory join channel and persist to .env."""
    async with _env_lock:
        if channel_id not in ADS_CHANNELS:
            return False

        ADS_CHANNELS.remove(channel_id)

        try:
            _update_env_keys({"TEL_ADS_CHANNELS": ",".join(ADS_CHANNELS)})
            logger.info(f"[CONFIG] Removed channel: {channel_id}")
            return True
        except Exception as e:
            ADS_CHANNELS.append(channel_id)
            logger.error(f"[CONFIG] Error removing channel: {e}")
            return False


async def add_admin(admin_id: int):
    """Add administrator and persist to .env."""
    async with _env_lock:
        if admin_id in ADMIN_IDS:
            return False

        ADMIN_IDS.append(admin_id)

        try:
            _update_env_keys({"TEL_ADMIN_IDS": ",".join(map(str, ADMIN_IDS))})
            logger.info(f"[CONFIG] Administrator added: {admin_id}")
            return True
        except Exception as e:
            ADMIN_IDS.remove(admin_id)
            logger.error(f"[CONFIG] Error adding admin: {e}")
            return False


async def remove_admin(admin_id: int):
    """Remove administrator and persist to .env."""
    async with _env_lock:
        if admin_id not in ADMIN_IDS:
            return False

        ADMIN_IDS.remove(admin_id)

        try:
            _update_env_keys({"TEL_ADMIN_IDS": ",".join(map(str, ADMIN_IDS))})
            logger.info(f"[CONFIG] Administrator removed: {admin_id}")
            return True
        except Exception as e:
            ADMIN_IDS.append(admin_id)
            logger.error(f"[CONFIG] Error removing admin: {e}")
            return False
