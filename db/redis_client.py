"""
مدیریت کلاینت و عملیات‌های Redis به صورت Asynchronous با قابلیت Fallback خودکار به حافظه.
"""
from typing import Any
import redis.asyncio as aioredis
from utils.logger import get_logger

logger = get_logger(__name__)

_redis_client: aioredis.Redis | None = None
_redis_available: bool = False


async def init_redis(redis_url: str | None) -> None:
    """راه‌اندازی اتصال به Redis در صورت تنظیم بودن REDIS_URL"""
    global _redis_client, _redis_available
    if not redis_url:
        _redis_available = False
        _redis_client = None
        logger.info("[REDIS] No REDIS_URL configured; using in-memory state store.")
        return

    try:
        client = aioredis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=3.0,
            socket_connect_timeout=3.0,
        )
        await client.ping()
        _redis_client = client
        _redis_available = True
        logger.info(f"[REDIS] Connected successfully to Redis: {redis_url}")
    except Exception as e:
        _redis_available = False
        _redis_client = None
        logger.error(f"[REDIS] Failed to connect to Redis ({redis_url}): {e}. Falling back to memory/sqlite.")


async def close_redis() -> None:
    """بستن سشن Redis در زمان خاموش شدن ربات"""
    global _redis_client, _redis_available
    if _redis_client:
        try:
            await _redis_client.aclose()
        except Exception:
            pass
        _redis_client = None
        _redis_available = False
        logger.info("[REDIS] Connection closed.")


def is_redis_available() -> bool:
    return _redis_available and _redis_client is not None


async def redis_set_state(tg_id: int, state: str, expire_seconds: int = 86400 * 7) -> bool:
    """ذخیره State کاربر در Redis با زمان انقضا"""
    if not is_redis_available():
        return False
    try:
        key = f"user:{tg_id}:state"
        await _redis_client.set(key, state, ex=expire_seconds)
        return True
    except Exception as e:
        logger.warning(f"[REDIS] set_state error for user {tg_id}: {e}")
        return False


async def redis_get_state(tg_id: int) -> str | None:
    """دریافت State کاربر از Redis"""
    if not is_redis_available():
        return None
    try:
        key = f"user:{tg_id}:state"
        val = await _redis_client.get(key)
        return val
    except Exception as e:
        logger.warning(f"[REDIS] get_state error for user {tg_id}: {e}")
        return None


async def redis_delete_state(tg_id: int) -> bool:
    """حذف State کاربر از Redis"""
    if not is_redis_available():
        return False
    try:
        key = f"user:{tg_id}:state"
        await _redis_client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"[REDIS] delete_state error for user {tg_id}: {e}")
        return False
