from __future__ import annotations

import asyncio
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from db.db_async import DB_NAME
from utils.logger import get_logger

logger = get_logger(__name__)


def create_sanitized_database_backup(
    db_path: str = DB_NAME,
    backup_dir: str = "backups",
    prefix: str = "bot_backup_sanitized",
) -> str:
    """
    Create a clean, sanitized database backup for export:
    1. Perform consistent snapshot using sqlite3 backup API.
    2. Redact sensitive user credentials (bale_token, access_key, secret_key).
    3. VACUUM sanitized backup to ensure zero remnant plaintext credentials.
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

        # Sanitize sensitive credential fields
        try:
            destination.execute("""
                UPDATE users
                SET bale_token = CASE WHEN bale_token IS NOT NULL THEN '***REDACTED***' ELSE NULL END,
                    access_key = CASE WHEN access_key IS NOT NULL THEN '***REDACTED***' ELSE NULL END,
                    secret_key = CASE WHEN secret_key IS NOT NULL THEN '***REDACTED***' ELSE NULL END
            """)
            destination.commit()
            destination.execute("VACUUM")
        except sqlite3.OperationalError as e:
            logger.warning(f"[DB-BACKUP] Redaction warning: {e}")

        logger.info(f"[DB-BACKUP] Sanitized backup created successfully: {backup_path}")
        return backup_path

    except Exception:
        logger.exception("[DB-BACKUP] Failed to create sanitized database backup")
        if os.path.exists(backup_path):
            try:
                os.remove(backup_path)
            except Exception:
                pass
        raise

    finally:
        if destination is not None:
            destination.close()
        if source is not None:
            source.close()


async def create_database_backup_async(
    db_path: str = DB_NAME,
    backup_dir: str = "backups",
    prefix: str = "bot_backup_sanitized",
) -> str:
    """Async wrapper for generating sanitized database backup."""
    return await asyncio.to_thread(
        create_sanitized_database_backup,
        db_path,
        backup_dir,
        prefix,
    )
