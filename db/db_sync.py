import sqlite3
from contextlib import contextmanager

from utils.logger import get_logger

logger = get_logger(__name__)

DB_NAME = "bot.db"


def create_connection() -> sqlite3.Connection:
    """ساخت و برگرداندن یک اتصال جدید به دیتابیس"""
    try:
        logger.debug(f"[DB-SYNC] Opening connection to {DB_NAME}")

        con = sqlite3.connect(DB_NAME)
        con.row_factory = sqlite3.Row

        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")

        logger.debug("[DB-SYNC] Connection established successfully")

        return con

    except Exception:
        logger.exception(
            f"[DB-SYNC] Failed to create database connection: {DB_NAME}"
        )
        raise


@contextmanager
def get_db():
    """
    Context manager برای مدیریت خودکار اتصال و تراکنش.

    استفاده:
        with get_db() as db:
            db.execute(...)
    """
    con = create_connection()

    try:
        logger.debug("[DB-SYNC] Transaction started")

        yield con

        con.commit()

        logger.debug("[DB-SYNC] Transaction committed successfully")

    except Exception:
        try:
            con.rollback()
            logger.warning(
                "[DB-SYNC] Transaction rolled back due to an exception"
            )
        except Exception:
            logger.exception(
                "[DB-SYNC] Failed to rollback transaction"
            )

        logger.exception(
            "[DB-SYNC] Unhandled exception during database transaction"
        )
        raise

    finally:
        try:
            con.close()
            logger.debug("[DB-SYNC] Connection closed")
        except Exception:
            logger.exception(
                "[DB-SYNC] Failed to close database connection"
            )