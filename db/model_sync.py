import sqlite3
 
from db.db_sync import get_db
from utils.logger import get_logger
 
logger = get_logger(__name__)
 
 
# ─────────────────────────────────────────────
#  Table Creation
# ─────────────────────────────────────────────
 
def create_tables() -> None:
    """ساخت تمامی جداول مورد نیاز (در صورت نبودن)"""
    with get_db() as db:
 
        # جدول کاربران
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id         INTEGER UNIQUE NOT NULL,
                bale_id             INTEGER UNIQUE,
                is_verified         INTEGER DEFAULT 0,
                is_banned           INTEGER DEFAULT 0,
                is_admin            INTEGER DEFAULT 0,
                state               TEXT    DEFAULT 'home',
                verify_code         INTEGER DEFAULT 0,
                verify_code_expire  TEXT    DEFAULT '',
                cooldown            TEXT    DEFAULT '',
                send_attempts       INTEGER DEFAULT 0,
                downloaded_volume   FLOAT   DEFAULT 0,
                limit_download      FLOAT   DEFAULT 0,
                created_at          TEXT    DEFAULT (datetime('now','localtime')),
                updated_at          TEXT    DEFAULT (datetime('now','localtime'))
            )
        """)

        # جدول پیام‌های پشتیبانی
        db.execute("""
            CREATE TABLE IF NOT EXISTS support_messages (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id     INTEGER NOT NULL,
                message_text    TEXT,
                is_read         INTEGER DEFAULT 0,
                sent_at         TEXT    DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
            )
        """)
 
    logger.info("[MODEL-SYNC][INFO] جداول با موفقیت ساخته شدند.")
 

def add_user(telegram_id: int, is_admin) -> bool:
    """افزودن کاربر جدید — True اگر جدید بود، False اگر از قبل بود"""
    if is_admin:
        is_admin = 1
    else:
        is_admin = 0
    with get_db() as db:
        cursor = db.execute("""
            INSERT OR IGNORE INTO users (telegram_id, is_admin)
            VALUES (? , ?)
        """, (telegram_id, is_admin))
        added = cursor.rowcount > 0
 
    if added:
        logger.info(f"[MODEL-SYNC][INFO] کاربر جدید اضافه شد: {telegram_id}")
    return added


