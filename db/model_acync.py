from db.db_async import get_async_db
from utils.logger import get_logger
 
logger = get_logger(__name__)


async def create_tables() -> None:
    """ساخت تمامی جداول مورد نیاز (در صورت نبودن)"""
    async with get_async_db() as db:
 
        await db.execute("""
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
                created_at          TEXT    DEFAULT (datetime('now','localtime')),
                updated_at          TEXT    DEFAULT (datetime('now','localtime'))
            )
        """)
 
 
        await db.execute("""
            CREATE TABLE IF NOT EXISTS support_messages (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id     INTEGER NOT NULL,
                message_text    TEXT,
                is_read         INTEGER DEFAULT 0,
                sent_at         TEXT    DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
            )
        """)
 
    logger.info("[MODEL-ASYNC][INFO] جداول با موفقیت ساخته شدند.")


async def is_user_exist(tg_id: int) -> bool:
    """بررسی وجود کاربر در دیتابیس با telegram_id"""
    async with get_async_db() as db:
        cursor = await db.execute(
            "SELECT 1 FROM users WHERE telegram_id = ?", (tg_id,)
        )
        return await cursor.fetchone() is not None



async def add_user(tg_id: int) -> bool:
    """افزودن کاربر جدید — True اگر جدید بود، False اگر از قبل بود"""
    async with get_async_db() as db:
        cursor = await db.execute("""
            INSERT OR IGNORE INTO users (telegram_id)
            VALUES (?)
        """, (tg_id,))
        added = cursor.rowcount > 0

    if added:
        logger.info(f"[MODEL-ASYNC][INFO] کاربر جدید اضافه شد: {tg_id}")
    else:
        logger.debug(f"[MODEL-ASYNC][DEBUG] کاربر از قبل موجود بود: {tg_id}")
    return added

async def check_admin(tg_id: int) -> bool:
    """بررسی ادمین بودن کاربر"""
    async with get_async_db() as db:
        cursor = await db.execute(
            "SELECT 1 FROM users WHERE telegram_id = ? AND is_admin = 1", (tg_id,)
        )
        return await cursor.fetchone() is not None


async def set_state(tg_id: int, state: str) -> None:
    """تغییر state کاربر"""
    async with get_async_db() as db:
        await db.execute("""
            UPDATE users
            SET state = ?, updated_at = datetime('now','localtime')
            WHERE telegram_id = ?
        """, (state, tg_id))
    logger.info(f"[MODEL-ASYNC][INFO] state کاربر {tg_id} به {state} تغییر کرد.")


async def check_ban(tg_id: int) -> bool:
    """بررسی بن بودن کاربر"""
    async with get_async_db() as db:
        cursor = await db.execute(
            "SELECT 1 FROM users WHERE telegram_id = ? AND is_banned = 1", (tg_id,)
        )
        return await cursor.fetchone() is not None


async def get_state(tg_id: int) -> str:
    """دریافت state فعلی کاربر"""
    async with get_async_db() as db:
        cursor = await db.execute(
            "SELECT state FROM users WHERE telegram_id = ?", (tg_id,)
        )
        row = await cursor.fetchone()
        return row["state"] if row else "home"


async def get_send_attempts(tg_id: int) -> int:
    """دریافت تعداد دفعات ارسال کد کاربر"""
    async with get_async_db() as db:
        cursor = await db.execute(
            "SELECT send_attempts FROM users WHERE telegram_id = ?", (tg_id,)
        )
        row = await cursor.fetchone()
        return row["send_attempts"] if row else 0


async def get_cooldown(tg_id: int) -> str:
    """دریافت cooldown کاربر"""
    async with get_async_db() as db:
        cursor = await db.execute(
            "SELECT cooldown FROM users WHERE telegram_id = ?", (tg_id,)
        )
        row = await cursor.fetchone()
        return row["cooldown"] if row else ""


async def set_send_attempts(tg_id: int, attempts: int) -> None:
    """تنظیم تعداد دفعات ارسال کد کاربر"""
    async with get_async_db() as db:
        await db.execute("""
            UPDATE users
            SET send_attempts = ?, updated_at = datetime('now','localtime')
            WHERE telegram_id = ?
        """, (attempts, tg_id))

async def set_verify_code(tg_id: int, code: int, expire: str) -> None:
    """ذخیره کد تأیید و زمان انقضای آن"""
    async with get_async_db() as db:
        await db.execute("""
            UPDATE users
            SET verify_code = ?, verify_code_expire = ?, updated_at = datetime('now','localtime')
            WHERE telegram_id = ?
        """, (code, expire, tg_id))

async def set_cooldown(tg_id: int, cooldown: str) -> None:
    """تنظیم cooldown کاربر"""
    async with get_async_db() as db:
        await db.execute("""
            UPDATE users
            SET cooldown = ?, updated_at = datetime('now','localtime')
            WHERE telegram_id = ?
        """, (cooldown, tg_id))

async def get_verify_code(tg_id: int) -> tuple[int, str]:
    """دریافت کد تأیید و زمان انقضای آن"""
    async with get_async_db() as db:
        cursor = await db.execute(
            "SELECT verify_code, verify_code_expire FROM users WHERE telegram_id = ?", (tg_id,)
        )
        row = await cursor.fetchone()
        return (row["verify_code"], row["verify_code_expire"]) if row else (0, "")

async def set_verified(tg_id: int, verified: bool = True) -> None:
    """تنظیم وضعیت تأیید کاربر"""
    async with get_async_db() as db:
        await db.execute("""
            UPDATE users
            SET is_verified = ?, updated_at = datetime('now','localtime')
            WHERE telegram_id = ?
        """, (int(verified), tg_id))

async def verify_check(tg_id: int) -> bool:
    """دریافت وضعیت تأیید کاربر"""
    async with get_async_db() as db:
        cursor = await db.execute(
            "SELECT is_verified FROM users WHERE telegram_id = ?", (tg_id,)
        )
        row = await cursor.fetchone()
        return bool(row["is_verified"]) if row else False

async def save_support_message(tg_id: int, message_text: str) -> None:
    """ذخیره پیام پشتیبانی کاربر"""
    async with get_async_db() as db:
        await db.execute("""
            INSERT INTO support_messages (telegram_id, message_text)
            VALUES (?, ?)
        """, (tg_id, message_text))
    logger.info(f"[MODEL-ASYNC][INFO] پیام پشتیبانی از {tg_id} ذخیره شد.")


async def get_telegram_ids_by_bale_id(bale_id: int) -> list[int]:
    """دریافت لیست telegram_id کاربرانی که bale_id آن‌ها برابر مقدار داده شده است"""
    async with get_async_db() as db:
        cursor = await db.execute(
            "SELECT telegram_id FROM users WHERE bale_id = ?", (bale_id,)
        )
        rows = await cursor.fetchall()
        return [row["telegram_id"] for row in rows]

async def ban_user(tg_id: int) -> bool:
    """بن کردن کاربر با telegram_id — True اگر موفق، False اگر کاربر پیدا نشد"""
    async with get_async_db() as db:
        cursor = await db.execute("""
            UPDATE users
            SET is_banned = 1, updated_at = datetime('now','localtime')
            WHERE telegram_id = ?
        """, (tg_id,))
        success = cursor.rowcount > 0
    if success:
        logger.warning(f"[MODEL-ASYNC][WARNING] کاربر بن شد: {tg_id}")
    return success

async def set_bale_id(tg_id: int, bale_id: int) -> None:
    """ثبت bale_id کاربر"""
    async with get_async_db() as db:
        await db.execute("""
            UPDATE users
            SET bale_id = ?, updated_at = datetime('now','localtime')
            WHERE telegram_id = ?
        """, (bale_id, tg_id))
    logger.info(f"[MODEL-ASYNC][INFO] bale_id کاربر {tg_id} به {bale_id} تنظیم شد.")


async def unban_user(tg_id: int) -> bool:
    """آنبن کردن کاربر با telegram_id — True اگر موفق، False اگر کاربر پیدا نشد"""
    async with get_async_db() as db:
        cursor = await db.execute("""
            UPDATE users
            SET is_banned = 0, updated_at = datetime('now','localtime')
            WHERE telegram_id = ?
        """, (tg_id,))
        success = cursor.rowcount > 0
    if success:
        logger.info(f"[MODEL-ASYNC][INFO] کاربر آنبن شد: {tg_id}")
    return success


async def get_top_users(limit: int = 10) -> list[dict]:
    """دریافت ۱۰ کاربر با بیشترین downloaded_volume"""
    async with get_async_db() as db:
        cursor = await db.execute("""
            SELECT telegram_id, bale_id, downloaded_volume
            FROM users
            ORDER BY downloaded_volume DESC
            LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        return [
            {
                "tg_id": row["telegram_id"],
                "bale_id": row["bale_id"],
                "downloaded_volume": round(float(row["downloaded_volume"]), 2)

            }
            for row in rows
        ]