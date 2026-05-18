import sqlite3
from contextlib import contextmanager
from utils.logger import get_logger

logger = get_logger(__name__)

DB_NAME = "bot.db"


def create_connection() -> sqlite3.Connection:
    """ساخت و برگرداندن یک اتصال جدید به دیتابیس"""
    con = sqlite3.connect(DB_NAME)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


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
        yield con
        con.commit()
    except Exception as e:
        con.rollback()
        logger.error(f"[DB-SYNC] خطا در تراکنش: {e}")
        raise
    finally:
        con.close()