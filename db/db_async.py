from contextlib import asynccontextmanager

import aiosqlite

from utils.logger import get_logger

logger = get_logger(__name__)

DB_NAME = "bot.db"


async def create_async_connection(
    isolation_level: str = "",
) -> aiosqlite.Connection:
    """ساخت و برگرداندن یک اتصال async جدید به دیتابیس"""
    try:
        logger.debug(f"[DB-ASYNC] Opening connection to {DB_NAME}")
        con = await aiosqlite.connect(DB_NAME, isolation_level=isolation_level)
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
            logger.exception("[DB-ASYNC] Failed to rollback transaction")

        logger.exception(
            "[DB-ASYNC] Unhandled exception during database transaction"
        )
        raise

    finally:
        try:
            await con.close()
            logger.debug("[DB-ASYNC] Connection closed")
        except Exception:
            logger.exception("[DB-ASYNC] Failed to close database connection")


@asynccontextmanager
async def get_async_db_immediate():
    """
    Async context manager با IMMEDIATE locking برای عملیات atomic read-then-write.

    چرا لازمه:
        در get_async_db معمولی، SQLite یک deferred lock می‌گیره.
        اگر دو coroutine همزمان SELECT کنن و بعد هر دو UPDATE بزنن،
        ممکنه یک row دو بار پردازش بشه (race condition).
        با BEGIN IMMEDIATE قبل از SELECT، write-lock فوری گرفته می‌شه
        و تضمین می‌شه فقط یک coroutine در لحظه این بلوک رو اجرا می‌کنه.

    isolation_level=None => حالت autocommit؛ تراکنش رو دستی مدیریت می‌کنیم
    تا با BEGIN/COMMIT/ROLLBACK صریح کنترل کامل داشته باشیم.

    استفاده:
        async with get_async_db_immediate() as db:
            row = await (await db.execute("SELECT ...")).fetchone()
            await db.execute("UPDATE ...")
    """
    con = await create_async_connection(isolation_level=None)

    try:
        await con.execute("BEGIN IMMEDIATE")
        logger.debug("[DB-ASYNC] IMMEDIATE transaction started")
        yield con
        await con.execute("COMMIT")
        logger.debug("[DB-ASYNC] IMMEDIATE transaction committed")

    except Exception:
        try:
            await con.execute("ROLLBACK")
            logger.warning("[DB-ASYNC] IMMEDIATE transaction rolled back")
        except Exception:
            logger.exception(
                "[DB-ASYNC] Failed to rollback IMMEDIATE transaction"
            )
        raise

    finally:
        try:
            await con.close()
            logger.debug("[DB-ASYNC] Connection closed")
        except Exception:
            logger.exception("[DB-ASYNC] Failed to close database connection")