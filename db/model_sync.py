from db.db_sync import get_db
from utils.logger import get_logger

logger = get_logger(__name__)


# ==================================================
# Tables
# ==================================================

def create_tables() -> None:
    """ساخت جداول مورد نیاز در صورت عدم وجود"""

    with get_db() as db:

        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id         INTEGER UNIQUE NOT NULL,
                bale_id             INTEGER DEFAULT NULL,
                is_banned           INTEGER DEFAULT 0,
                is_admin            INTEGER DEFAULT 0,
                state               TEXT    DEFAULT 'home',
                bale_token          TEXT    DEFAULT NULL,
                s3_endpoint         TEXT    DEFAULT NULL,
                access_key          TEXT    DEFAULT NULL,
                secret_key          TEXT    DEFAULT NULL,
                downloaded_volume   FLOAT   DEFAULT 0,
                limit_download      FLOAT   DEFAULT 0,
                support_message_count INTEGER DEFAULT 0,
                created_at          TEXT DEFAULT (
                    datetime('now','localtime')
                ),
                updated_at          TEXT DEFAULT (
                    datetime('now','localtime')
                )
            )
        """)

        try:
            db.execute("ALTER TABLE users ADD COLUMN support_message_count INTEGER DEFAULT 0")
        except Exception:
            pass

        db.execute("""
            CREATE TABLE IF NOT EXISTS support_messages (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id         INTEGER NOT NULL,
                group_message_id    INTEGER NOT NULL UNIQUE,
                is_answered         INTEGER DEFAULT 0,
                created_at          TEXT DEFAULT (
                    datetime('now','localtime')
                )
            )
        """)

    logger.info(
        "[MODEL-SYNC] Database tables created successfully"
    )


# ==================================================
# Users
# ==================================================

def add_user(
    telegram_id: int,
    is_admin: bool = False
) -> bool:
    """
    افزودن کاربر جدید

    Returns:
        True  -> کاربر اضافه شد
        False -> کاربر از قبل وجود داشت
    """

    with get_db() as db:

        cursor = db.execute("""
            INSERT OR IGNORE INTO users (
                telegram_id,
                is_admin
            )
            VALUES (?, ?)
        """, (
            telegram_id,
            int(is_admin)
        ))

        try:
            added = cursor.rowcount > 0
        finally:
            cursor.close()

    if added:
        logger.info(
            f"[MODEL-SYNC] New user added: "
            f"{telegram_id}"
        )

    return added