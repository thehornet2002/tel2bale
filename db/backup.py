from __future__ import annotations

import asyncio
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from db.db_sync import DB_NAME
from utils.logger import get_logger

logger = get_logger(__name__)


def create_database_backup(
    db_path: str = DB_NAME,
    backup_dir: str = "backups",
    prefix: str = "bot_backup",
) -> str:
    """
    یک backup سالم و سازگار از SQLite می‌سازد و مسیر فایل backup را برمی‌گرداند.

    نکته:
    وقتی SQLite در حالت WAL باشد، کپی ساده bot.db کافی نیست؛ چون ممکن است بخشی
    از تغییرات داخل bot.db-wal باشد. sqlite backup API یک snapshot سالم می‌سازد.
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    Path(backup_dir).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"{prefix}_{timestamp}.db")

    source: sqlite3.Connection | None = None
    destination: sqlite3.Connection | None = None

    try:
        source = sqlite3.connect(db_path, timeout=30)
        destination = sqlite3.connect(backup_path, timeout=30)

        source.execute("PRAGMA busy_timeout = 5000")
        destination.execute("PRAGMA busy_timeout = 5000")

        source.backup(destination)
        destination.commit()

        logger.info(f"[DB-BACKUP] Backup created successfully: {backup_path}")
        return backup_path

    except Exception:
        logger.exception("[DB-BACKUP] Failed to create database backup")

        if os.path.exists(backup_path):
            try:
                os.remove(backup_path)
            except Exception:
                logger.exception("[DB-BACKUP] Failed to remove broken backup file")

        raise

    finally:
        if destination is not None:
            destination.close()

        if source is not None:
            source.close()


async def create_database_backup_async(
    db_path: str = DB_NAME,
    backup_dir: str = "backups",
    prefix: str = "bot_backup",
) -> str:
    """
    نسخه async برای استفاده داخل handlerها.

    چون backup گرفتن یک کار sync است، با asyncio.to_thread اجرا می‌شود
    تا event loop ربات بلاک نشود.
    """
    return await asyncio.to_thread(
        create_database_backup,
        db_path,
        backup_dir,
        prefix,
    )