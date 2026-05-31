from contextlib import asynccontextmanager

import aiosqlite

from utils.logger import get_logger

logger = get_logger(__name__)

DB_NAME = "bot.db"


async def create_async_connection() -> aiosqlite.Connection:
    """ساخت و برگرداندن یک اتصال async جدید به دیتابیس"""
    try:
        logger.debug(f"[DB-ASYNC] Opening connection to {DB_NAME}")
        con = await aiosqlite.connect(DB_NAME)
        con.row_factory = aiosqlite.Row
        await con.execute("PRAGMA journal_mode=WAL")
        await con.execute("PRAGMA foreign_keys=ON")
        logger.debug("[DB-ASYNC] Connection established successfully")
        return con

    except Exception:
        logger.exception(
            f"[DB-ASYNC] Failed to create database connection: {DB_NAME}"
        )
        raise


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
        logger.debug("[DB-ASYNC] Transaction started")
        yield con
        await con.commit()
        logger.debug("[DB-ASYNC] Transaction committed successfully")

    except Exception:
        try:
            await con.rollback()
            logger.warning(
                "[DB-ASYNC] Transaction rolled back due to an exception"
            )
        except Exception:
            logger.exception(
                "[DB-ASYNC] Failed to rollback transaction"
            )

        logger.exception(
            "[DB-ASYNC] Unhandled exception during database transaction"
        )
        raise

    finally:
        try:
            await con.close()
            logger.debug("[DB-ASYNC] Connection closed")
        except Exception:
            logger.exception(
                "[DB-ASYNC] Failed to close database connection"
            )