from contextlib import asynccontextmanager

import aiosqlite

from utils.logger import get_logger

logger = get_logger(__name__)

DB_NAME = "bot.db"


async def create_async_connection() -> aiosqlite.Connection:
    """ساخت و برگرداندن یک اتصال async جدید به دیتابیس"""
    con = await aiosqlite.connect(DB_NAME)
    con.row_factory = aiosqlite.Row
    await con.execute("PRAGMA journal_mode=WAL")
    await con.execute("PRAGMA foreign_keys=ON")
    return con


@asynccontextmanager
async def get_async_db():
    """
    Async context manager برای مدیریت خودکار اتصال و تراکنش.

    استفاده:
        async with get_async_db() as db:
            await db.execute(...)
    """
    con = await create_async_connection()
    try:
        yield con
        await con.commit()
    except Exception as e:
        await con.rollback()
        logger.error(f"[DB-ASYNC] خطا در تراکنش: {e}")
        raise
    finally:
        await con.close()