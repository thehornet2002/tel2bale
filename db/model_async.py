from typing import Any

import config
from db.db_async import get_async_db, get_async_db_immediate
from db.redis_client import (
    init_redis,
    close_redis,
    is_redis_available,
    redis_get_state,
    redis_set_state,
    redis_delete_state,
)
from utils.logger import get_logger

logger = get_logger(__name__)


# =========================
# Field allowlists
#
# هر فیلدی که مستقیم داخل SQL string قرار می‌گیره
# باید اول در این frozenset ها تأیید بشه.
# این از SQL injection جلوگیری می‌کنه.
# =========================

_USER_READABLE_FIELDS: frozenset[str] = frozenset({
    "telegram_id", "bale_id", "is_banned", "is_admin",
    "state", "bale_token", "access_key", "secret_key",
    "downloaded_volume", "limit_download", "support_message_count",
    "created_at", "updated_at", "s3_endpoint",
})

_USER_UPDATABLE_FIELDS: frozenset[str] = frozenset({
    "bale_id", "is_banned", "is_admin", "state",
    "bale_token", "access_key", "secret_key",
    "downloaded_volume", "limit_download", "s3_endpoint",
    "support_message_count",
})

_LIMIT_VOLUME: float = 0.0

# =========================
# In-Memory Fast Cache
# =========================
_EXISTING_USERS: set[int] = set()
_ADMIN_USERS: set[int] = set()
_BANNED_USERS: set[int] = set()
_STATE_CACHE: dict[int, str] = {}
_BALE_ID_CACHE: dict[int, int | None] = {}
_BALE_TOKEN_CACHE: dict[int, str] = {}
_WHITELIST_USERS: set[int] = set()
_WHITELIST_ENABLED: bool = False
_CAPTCHA_TICKET_ENABLED: bool = True
_CAPTCHA_POLL_ENABLED: bool = False
_CAPTCHA_FILE_ENABLED: bool = False

# =========================
# Tables & Settings
# =========================

async def create_tables() -> None:
    """ساخت جداول مورد نیاز در صورت عدم وجود (نسخه کاملاً async)"""
    async with get_async_db() as db:
        await db.execute("""
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
                created_at          TEXT DEFAULT (datetime('now','localtime')),
                updated_at          TEXT DEFAULT (datetime('now','localtime'))
            )
        """)

        try:
            await db.execute("ALTER TABLE users ADD COLUMN support_message_count INTEGER DEFAULT 0")
        except Exception:
            pass

        await db.execute("""
            CREATE TABLE IF NOT EXISTS support_messages (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id         INTEGER NOT NULL,
                group_message_id    INTEGER NOT NULL UNIQUE,
                is_answered         INTEGER DEFAULT 0,
                created_at          TEXT DEFAULT (datetime('now','localtime'))
            )
        """)

        # جدول دسته‌بندی‌های تیکت (الگوبرداری از سیستم Senfi)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ticket_categories (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                title        TEXT UNIQUE NOT NULL,
                is_active    INTEGER DEFAULT 1,
                is_anonymous INTEGER DEFAULT 0,
                created_at   TEXT DEFAULT (datetime('now','localtime'))
            )
        """)

        try:
            await db.execute("ALTER TABLE ticket_categories ADD COLUMN is_anonymous INTEGER DEFAULT 0")
        except Exception:
            pass

        # جدول اصلی تیکت‌های پشتیبانی
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id         INTEGER NOT NULL,
                user_name           TEXT,
                category_id         INTEGER DEFAULT 1,
                subject             TEXT,
                message             TEXT NOT NULL,
                reply               TEXT DEFAULT NULL,
                status              TEXT DEFAULT 'خوانده نشده',
                is_anonymous        INTEGER DEFAULT 0,
                group_message_id    INTEGER DEFAULT NULL,
                created_at          TEXT DEFAULT (datetime('now','localtime')),
                updated_at          TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (category_id) REFERENCES ticket_categories (id)
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tickets_user ON tickets (telegram_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets (status)")

        try:
            await db.execute("ALTER TABLE tickets ADD COLUMN is_anonymous INTEGER DEFAULT 0")
        except Exception:
            pass

        # اضافه کردن دسته‌بندی‌های پیش‌فرض
        cursor = await db.execute("SELECT COUNT(*) AS cnt FROM ticket_categories")
        cat_cnt = (await cursor.fetchone())["cnt"]
        if cat_cnt == 0:
            defaults = ["پشتیبانی عمومی", "مشکلات فنی و اتصال", "پیشنهادات و انتقادات"]
            for title in defaults:
                await db.execute("INSERT OR IGNORE INTO ticket_categories (title) VALUES (?)", (title,))

        # جدول نظرسنجی‌ها (پشتیبانی از چندین نظرسنجی هم‌زمان و عنوان)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS polls (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT,
                question    TEXT NOT NULL,
                options     TEXT NOT NULL,
                is_active   INTEGER DEFAULT 1,
                created_at  TEXT DEFAULT (datetime('now','localtime'))
            )
        """)

        try:
            await db.execute("ALTER TABLE polls ADD COLUMN title TEXT")
        except Exception:
            pass

        # جدول آرای نظرسنجی
        await db.execute("""
            CREATE TABLE IF NOT EXISTS poll_votes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id     INTEGER NOT NULL,
                telegram_id INTEGER NOT NULL,
                option_idx  INTEGER NOT NULL,
                created_at  TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(poll_id, telegram_id)
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_poll_votes ON poll_votes (poll_id, telegram_id)")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS whitelist (
                telegram_id INTEGER PRIMARY KEY
            )
        """)

    await init_cache()
    await init_redis(config.REDIS_URL)
    logger.info("[MODEL-ASYNC] Database tables and in-memory cache initialized successfully")


async def init_cache() -> None:
    """لود تمام داده‌های پردرخواست به حافظه RAM جهت بهینه‌سازی سرعت و حذف کوئری‌های تکراری"""
    global _WHITELIST_ENABLED, _LIMIT_VOLUME
    _EXISTING_USERS.clear()
    _ADMIN_USERS.clear()
    _BANNED_USERS.clear()
    _STATE_CACHE.clear()
    _BALE_ID_CACHE.clear()
    _BALE_TOKEN_CACHE.clear()
    _WHITELIST_USERS.clear()

    async with get_async_db() as db:
        cursor = await db.execute("SELECT telegram_id, is_admin, is_banned, state, bale_id, bale_token FROM users")
        try:
            rows = await cursor.fetchall()
            for row in rows:
                t_id = row["telegram_id"]
                _EXISTING_USERS.add(t_id)
                if row["is_admin"]:
                    _ADMIN_USERS.add(t_id)
                if row["is_banned"]:
                    _BANNED_USERS.add(t_id)
                if row["state"]:
                    _STATE_CACHE[t_id] = row["state"]
                _BALE_ID_CACHE[t_id] = row["bale_id"]
                _BALE_TOKEN_CACHE[t_id] = row["bale_token"] or ""
        finally:
            await cursor.close()

        cursor = await db.execute("SELECT telegram_id FROM whitelist")
        try:
            w_rows = await cursor.fetchall()
            for r in w_rows:
                _WHITELIST_USERS.add(r["telegram_id"])
        finally:
            await cursor.close()

    import config
    for admin_id in config.ADMIN_IDS:
        _ADMIN_USERS.add(admin_id)

    for w_id in config.WHITELIST_USERS:
        _WHITELIST_USERS.add(w_id)

    saved_limit = await get_setting("default_limit_volume", "")
    if saved_limit:
        try:
            _LIMIT_VOLUME = float(saved_limit)
        except ValueError:
            pass

    saved_wl = await get_setting("whitelist_enabled", "")
    if saved_wl:
        _WHITELIST_ENABLED = (saved_wl.lower() == "true")
    else:
        _WHITELIST_ENABLED = config.WHITELIST_ENABLED

    if _WHITELIST_ENABLED:
        admin_ids = set(_ADMIN_USERS).union(config.ADMIN_IDS)
        for admin_id in admin_ids:
            _WHITELIST_USERS.add(admin_id)

    global _CAPTCHA_TICKET_ENABLED, _CAPTCHA_POLL_ENABLED, _CAPTCHA_FILE_ENABLED
    saved_ct = await get_setting("captcha_ticket_enabled", "true")
    _CAPTCHA_TICKET_ENABLED = (saved_ct.lower() == "true")
    saved_cp = await get_setting("captcha_poll_enabled", "false")
    _CAPTCHA_POLL_ENABLED = (saved_cp.lower() == "true")
    saved_cf = await get_setting("captcha_file_enabled", "false")
    _CAPTCHA_FILE_ENABLED = (saved_cf.lower() == "true")


async def get_setting(key: str, default: str = "") -> str:
    row = await _fetchone("SELECT value FROM settings WHERE key = ?", (key,))
    return row["value"] if row else default


async def set_setting(key: str, value: str) -> bool:
    async with get_async_db() as db:
        await db.execute("""
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, value))
    return True


# =========================
# Helpers
# =========================

async def _fetchone(query: str, params: tuple = ()) -> dict | None:
    async with get_async_db() as db:
        cursor = await db.execute(query, params)
        try:
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await cursor.close()


async def _fetchall(query: str, params: tuple = ()) -> list[dict]:
    async with get_async_db() as db:
        cursor = await db.execute(query, params)
        try:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await cursor.close()


async def _execute(query: str, params: tuple = ()) -> bool:
    async with get_async_db() as db:
        cursor = await db.execute(query, params)
        try:
            return cursor.rowcount > 0
        finally:
            await cursor.close()

async def set_limit_volume(limit_volume: float):
    global _LIMIT_VOLUME
    _LIMIT_VOLUME = limit_volume
    await set_setting("default_limit_volume", str(limit_volume))



async def _get_user_field(
    tg_id: int,
    field: str,
    default: Any = None,
) -> Any:
    """
    یک فیلد از جدول users رو برمی‌گردونه.

    Bug fix: قبلاً field مستقیم داخل f-string قرار می‌گرفت (SQL injection).
    الان فقط فیلدهایی که در _USER_READABLE_FIELDS هستن مجاز هستن.
    """
    if field not in _USER_READABLE_FIELDS:
        raise ValueError(
            f"[MODEL-ASYNC] Invalid field name for SELECT: {field!r}"
        )

    row = await _fetchone(
        f"SELECT {field} FROM users WHERE telegram_id = ?",
        (tg_id,),
    )
    if row is None:
        return default
    return row.get(field, default)


async def _update_user_field(
    tg_id: int,
    field: str,
    value: Any,
) -> bool:
    """
    یک فیلد از جدول users رو آپدیت می‌کنه و updated_at رو هم تنظیم می‌کنه.

    تمام set_* هایی که الگوی یکسانی دارن از این تابع استفاده می‌کنن
    تا تکرار کد و احتمال SQL injection حذف بشه.
    """
    if field not in _USER_UPDATABLE_FIELDS:
        raise ValueError(
            f"[MODEL-ASYNC] Invalid field name for UPDATE: {field!r}"
        )

    return await _execute(f"""
        UPDATE users
        SET {field} = ?,
            updated_at = datetime('now','localtime')
        WHERE telegram_id = ?
    """, (value, tg_id))


# =========================
# User existence / status
# =========================

async def is_user_exist(tg_id: int) -> bool:
    if tg_id in _EXISTING_USERS:
        return True
    row = await _fetchone(
        "SELECT 1 FROM users WHERE telegram_id = ?",
        (tg_id,),
    )
    if row is not None:
        _EXISTING_USERS.add(tg_id)
        return True
    return False


async def add_user(tg_id: int, is_admin: bool = False) -> bool:
    _EXISTING_USERS.add(tg_id)
    _STATE_CACHE[tg_id] = "home"
    if is_admin:
        _ADMIN_USERS.add(tg_id)

    async with get_async_db() as db:
        cursor = await db.execute("""
            INSERT OR IGNORE INTO users (telegram_id, is_admin, limit_download)
            VALUES (?, ?, ?)
        """, (tg_id, int(is_admin), _LIMIT_VOLUME))
        try:
            added = cursor.rowcount > 0
        finally:
            await cursor.close()

    if added:
        logger.info(f"[MODEL-ASYNC] User added: {tg_id}")
    return added


async def check_admin(tg_id: int) -> bool:
    return tg_id in _ADMIN_USERS


async def check_ban(tg_id: int) -> bool:
    return tg_id in _BANNED_USERS


# =========================
# State
# =========================

async def set_state(tg_id: int, state: str) -> bool:
    _STATE_CACHE[tg_id] = state
    # در صورت وجود ردیس، اول در ردیس ذخیره شود
    if is_redis_available():
        await redis_set_state(tg_id, state)

    success = await _update_user_field(tg_id, "state", state)
    if success:
        logger.debug(f"[MODEL-ASYNC] State changed for user {tg_id}: {state}")
    return success


async def get_state(tg_id: int) -> str:
    # 1. اگر در ردیس مقدار بود، اولویت با ردیس است
    if is_redis_available():
        r_state = await redis_get_state(tg_id)
        if r_state is not None:
            _STATE_CACHE[tg_id] = r_state
            return r_state

    # 2. در صورت نبود ردیس، کش RAM
    if tg_id in _STATE_CACHE:
        return _STATE_CACHE[tg_id]

    # 3. دیتابیس SQLite
    state = await _get_user_field(tg_id, "state", "home")
    _STATE_CACHE[tg_id] = state
    if is_redis_available():
        await redis_set_state(tg_id, state)
    return state


# =========================
# Bale ID
# =========================

async def get_bale_id(tg_id: int) -> int | None:
    if tg_id in _BALE_ID_CACHE:
        return _BALE_ID_CACHE[tg_id]
    val = await _get_user_field(tg_id, "bale_id", None)
    _BALE_ID_CACHE[tg_id] = val
    return val


async def set_bale_id(tg_id: int, bale_id: int) -> bool:
    _BALE_ID_CACHE[tg_id] = bale_id
    success = await _update_user_field(tg_id, "bale_id", bale_id)
    if success:
        logger.debug(f"[MODEL-ASYNC] Bale ID updated for user {tg_id}")
    return success


async def get_telegram_ids_by_bale_id(bale_id: int) -> list[int]:
    rows = await _fetchall(
        "SELECT telegram_id FROM users WHERE bale_id = ?",
        (bale_id,),
    )
    return [row["telegram_id"] for row in rows]


# =========================
# Download limits
# =========================

async def get_downloaded_volume(tg_id: int) -> float:
    return float(await _get_user_field(tg_id, "downloaded_volume", 0.0))


async def set_downloaded_volume(tg_id: int, volume: float) -> bool:
    return await _update_user_field(tg_id, "downloaded_volume", volume)


async def get_limit_download(tg_id: int) -> float:
    return float(await _get_user_field(tg_id, "limit_download", 0.0))


async def set_limit_download(tg_id: int, limit: float) -> bool:
    success = await _update_user_field(tg_id, "limit_download", limit)
    if success:
        logger.debug(f"[MODEL-ASYNC] Download limit updated for user {tg_id}")
    return success

async def reserve_download_quota(tg_id: int, file_size_bytes: int | None) -> bool:
    """
    Atomically checks and reserves user download quota.

    Why this must be atomic:
        A separate SELECT followed by UPDATE can race when the same user sends
        multiple files at the same time. BEGIN IMMEDIATE serializes this
        read-then-write block, so downloaded_volume is updated correctly.

    Returns:
        True  -> quota is available and downloaded_volume was updated
        False -> user does not exist or quota limit would be exceeded
    """
    if not file_size_bytes or file_size_bytes <= 0:
        return True

    file_size_gb = file_size_bytes / (1024 ** 3)

    async with get_async_db_immediate() as db:
        cursor = await db.execute("""
            SELECT downloaded_volume, limit_download
            FROM users
            WHERE telegram_id = ?
        """, (tg_id,))
        try:
            row = await cursor.fetchone()
        finally:
            await cursor.close()

        if row is None:
            logger.warning(
                f"[MODEL-ASYNC] Quota reservation failed; user not found: {tg_id}"
            )
            return False

        downloaded_volume = float(row["downloaded_volume"] or 0.0)
        limit_download = float(row["limit_download"] or 0.0)
        new_downloaded_volume = downloaded_volume + file_size_gb

        if limit_download != 0 and new_downloaded_volume > limit_download:
            logger.info(
                f"[MODEL-ASYNC] Quota exceeded for user {tg_id}: "
                f"current={downloaded_volume:.6f}GB, "
                f"file={file_size_gb:.6f}GB, limit={limit_download:.6f}GB"
            )
            return False

        await db.execute("""
            UPDATE users
            SET downloaded_volume = ?,
                updated_at = datetime('now','localtime')
            WHERE telegram_id = ?
        """, (new_downloaded_volume, tg_id))

        logger.debug(
            f"[MODEL-ASYNC] Quota reserved for user {tg_id}: "
            f"{new_downloaded_volume:.6f}GB"
        )
        return True


async def release_download_quota(tg_id: int, file_size_bytes: int | None) -> bool:
    """
    Atomically rolls back a previously reserved quota amount.
    Use this when the transfer/upload fails after reserve_download_quota succeeded.
    """
    if not file_size_bytes or file_size_bytes <= 0:
        return True

    file_size_gb = file_size_bytes / (1024 ** 3)

    async with get_async_db_immediate() as db:
        cursor = await db.execute("""
            SELECT downloaded_volume
            FROM users
            WHERE telegram_id = ?
        """, (tg_id,))
        try:
            row = await cursor.fetchone()
        finally:
            await cursor.close()

        if row is None:
            logger.warning(
                f"[MODEL-ASYNC] Quota release failed; user not found: {tg_id}"
            )
            return False

        downloaded_volume = float(row["downloaded_volume"] or 0.0)
        new_downloaded_volume = max(0.0, downloaded_volume - file_size_gb)

        await db.execute("""
            UPDATE users
            SET downloaded_volume = ?,
                updated_at = datetime('now','localtime')
            WHERE telegram_id = ?
        """, (new_downloaded_volume, tg_id))

        logger.debug(
            f"[MODEL-ASYNC] Quota released for user {tg_id}: "
            f"{new_downloaded_volume:.6f}GB"
        )
        return True


async def set_limit_download_all(limit: float) -> None:
    # این تابع همه کاربران رو آپدیت می‌کنه (بدون WHERE)،
    # پس از _update_user_field که per-user است نمی‌شه استفاده کرد.
    async with get_async_db() as db:
        await db.execute("""
            UPDATE users
            SET limit_download = ?,
                updated_at = datetime('now','localtime')
        """, (limit,))

    logger.info(f"[MODEL-ASYNC] Global download limit set to {limit}")


# =========================
# Ban / Unban
# =========================

async def ban_user(tg_id: int) -> bool:
    if tg_id in _ADMIN_USERS or tg_id in config.ADMIN_IDS:
        logger.warning(f"[MODEL-ASYNC] Cannot ban admin user: {tg_id}")
        return False
    _BANNED_USERS.add(tg_id)
    success = await _update_user_field(tg_id, "is_banned", 1)
    if success:
        logger.warning(f"[MODEL-ASYNC] User banned: {tg_id}")
    return success


async def unban_user(tg_id: int) -> bool:
    _BANNED_USERS.discard(tg_id)
    success = await _update_user_field(tg_id, "is_banned", 0)
    if success:
        logger.info(f"[MODEL-ASYNC] User unbanned: {tg_id}")
    return success


# =========================
# Admin
# =========================

async def set_admin(tg_id: int) -> bool:
    _ADMIN_USERS.add(tg_id)
    success = await _update_user_field(tg_id, "is_admin", 1)
    if success:
        logger.info(f"[MODEL-ASYNC] User promoted to admin: {tg_id}")
        if _WHITELIST_ENABLED:
            await add_to_whitelist(tg_id)
    return success


async def unset_admin(tg_id: int) -> bool:
    _ADMIN_USERS.discard(tg_id)
    success = await _update_user_field(tg_id, "is_admin", 0)
    if success:
        logger.info(f"[MODEL-ASYNC] Admin removed: {tg_id}")
    return success


# =========================
# Statistics
# =========================

async def get_top_users(limit: int = 10) -> list[dict]:
    rows = await _fetchall("""
        SELECT telegram_id, bale_id, downloaded_volume
        FROM users
        ORDER BY downloaded_volume DESC
        LIMIT ?
    """, (limit,))

    return [
        {
            "tg_id": row["telegram_id"],
            "bale_id": row["bale_id"],
            "downloaded_volume": round(float(row["downloaded_volume"]), 2),
        }
        for row in rows
    ]


async def get_all_telegram_ids() -> list[int]:
    rows = await _fetchall("SELECT telegram_id FROM users")
    return [row["telegram_id"] for row in rows]



# =========================
# Arvan Storage credentials
# =========================

async def get_access_key(tg_id: int) -> str | None:
    return await _get_user_field(tg_id, "access_key", None)


async def set_access_key(tg_id: int, access_key: str) -> bool:
    return await _update_user_field(tg_id, "access_key", access_key)


async def get_secret_key(tg_id: int) -> str | None:
    return await _get_user_field(tg_id, "secret_key", None)


async def set_secret_key(tg_id: int, secret_key: str) -> bool:
    return await _update_user_field(tg_id, "secret_key", secret_key)


async def get_bale_token(tg_id: int) -> str:
    if tg_id in _BALE_TOKEN_CACHE:
        return _BALE_TOKEN_CACHE[tg_id]
    val = await _get_user_field(tg_id, "bale_token", "") or ""
    _BALE_TOKEN_CACHE[tg_id] = val
    return val


async def set_bale_token(tg_id: int, bale_token: str) -> bool:
    _BALE_TOKEN_CACHE[tg_id] = bale_token
    return await _update_user_field(tg_id, "bale_token", bale_token)

async def get_s3_endpoint(tg_id: int) -> str | None:
    return await _get_user_field(tg_id, "s3_endpoint", None)


async def set_s3_endpoint(tg_id: int, s3_endpoint: str) -> bool:
    return await _update_user_field(tg_id, "s3_endpoint", s3_endpoint)

# =========================
# Support & Ticket System (سیستم پیشرفته تیکتینگ الگوبرداری از Senfi)
# =========================

STATUS_UNREAD = "خوانده نشده"
STATUS_ANSWERED = "پاسخ داده شده"
STATUS_CLOSED = "بسته شده"


async def get_ticket_categories(active_only: bool = True) -> list[dict]:
    query = "SELECT * FROM ticket_categories WHERE is_active = 1 ORDER BY id ASC" if active_only else "SELECT * FROM ticket_categories ORDER BY id ASC"
    rows = await _fetchall(query)
    return [dict(r) for r in rows]


async def get_ticket_category(category_id: int) -> dict | None:
    row = await _fetchone("SELECT * FROM ticket_categories WHERE id = ?", (category_id,))
    return dict(row) if row else None


async def add_ticket_category(title: str, is_anonymous: int = 0) -> bool:
    async with get_async_db() as db:
        await db.execute("""
            INSERT OR IGNORE INTO ticket_categories (title, is_active, is_anonymous)
            VALUES (?, 1, ?)
        """, (title.strip(), is_anonymous))
    return True


async def delete_ticket_category(category_id: int, delete_tickets: bool = False) -> tuple[bool, int]:
    async with get_async_db() as db:
        if delete_tickets:
            cursor = await db.execute("DELETE FROM tickets WHERE category_id = ?", (category_id,))
            del_count = cursor.rowcount
            await db.execute("DELETE FROM ticket_categories WHERE id = ?", (category_id,))
            return True, del_count
        else:
            await db.execute("UPDATE ticket_categories SET is_active = 0 WHERE id = ?", (category_id,))
            return True, 0


async def count_tickets_by_category() -> list[dict]:
    query = """
        SELECT c.id, c.title, c.is_active, c.is_anonymous, COUNT(t.id) AS ticket_count
        FROM ticket_categories c
        LEFT JOIN tickets t ON c.id = t.category_id
        GROUP BY c.id
        ORDER BY c.id ASC
    """
    rows = await _fetchall(query)
    return [dict(r) for r in rows]


async def create_user_ticket(
    telegram_id: int,
    user_name: str,
    category_id: int,
    message: str,
    subject: str = "پشتیبانی",
    is_anonymous: int = 0,
    group_message_id: int | None = None,
) -> int:
    async with get_async_db() as db:
        cursor = await db.execute("""
            INSERT INTO tickets (telegram_id, user_name, category_id, subject, message, status, is_anonymous, group_message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (telegram_id, user_name, category_id, subject, message.strip(), STATUS_UNREAD, is_anonymous, group_message_id))
        return cursor.lastrowid or 0


async def get_user_tickets(telegram_id: int) -> list[dict]:
    query = """
        SELECT t.*, c.title AS category_title
        FROM tickets t
        LEFT JOIN ticket_categories c ON t.category_id = c.id
        WHERE t.telegram_id = ?
        ORDER BY t.id DESC
        LIMIT 15
    """
    rows = await _fetchall(query, (telegram_id,))
    return [dict(r) for r in rows]


async def get_ticket(ticket_id: int) -> dict | None:
    query = """
        SELECT t.*, c.title AS category_title
        FROM tickets t
        LEFT JOIN ticket_categories c ON t.category_id = c.id
        WHERE t.id = ?
    """
    row = await _fetchone(query, (ticket_id,))
    return dict(row) if row else None


async def answer_ticket(ticket_id: int, reply_text: str) -> bool:
    async with get_async_db() as db:
        await db.execute("""
            UPDATE tickets
            SET reply = ?, status = ?, updated_at = datetime('now','localtime')
            WHERE id = ?
        """, (reply_text.strip(), STATUS_ANSWERED, ticket_id))
    return True


async def get_ticket_by_group_message_id(group_message_id: int) -> dict | None:
    query = """
        SELECT t.*, c.title AS category_title
        FROM tickets t
        LEFT JOIN ticket_categories c ON t.category_id = c.id
        WHERE t.group_message_id = ?
    """
    row = await _fetchone(query, (group_message_id,))
    return dict(row) if row else None


async def get_support_message_count(tg_id: int) -> int:
    return int(await _get_user_field(tg_id, "support_message_count", 0) or 0)


async def increment_support_message_count(tg_id: int) -> bool:
    return await _execute("""
        UPDATE users
        SET support_message_count = support_message_count + 1,
            updated_at = datetime('now','localtime')
        WHERE telegram_id = ?
    """, (tg_id,))


async def reset_support_message_count(tg_id: int) -> bool:
    return await _update_user_field(tg_id, "support_message_count", 0)


async def save_support_message(tg_id: int, group_message_id: int) -> bool:
    """ذخیره پیام ارسالی کاربر به گروه پشتیبانی برای تطبیق بعدی با ریپلای ادمین"""
    async with get_async_db() as db:
        await db.execute("""
            INSERT INTO support_messages (telegram_id, group_message_id)
            VALUES (?, ?)
        """, (tg_id, group_message_id))
    return True


async def get_telegram_id_by_group_message(group_message_id: int) -> int | None:
    # ابتدا در جدول تیکت‌ها جستجو کن
    ticket = await get_ticket_by_group_message_id(group_message_id)
    if ticket:
        return ticket["telegram_id"]

    row = await _fetchone(
        """
        SELECT telegram_id FROM support_messages
        WHERE group_message_id = ? AND is_answered = 0
        """,
        (group_message_id,),
    )
    return row["telegram_id"] if row else None


async def mark_support_message_answered(group_message_id: int) -> bool:
    async with get_async_db() as db:
        await db.execute("""
            UPDATE tickets
            SET status = ?, updated_at = datetime('now','localtime')
            WHERE group_message_id = ?
        """, (STATUS_ANSWERED, group_message_id))
    return await _execute(
        "UPDATE support_messages SET is_answered = 1 WHERE group_message_id = ?",
        (group_message_id,),
    )

async def get_tickets_paged(
    status: str | None = None,
    category_id: int = 0,
    page: int = 1,
    per_page: int = 10,
) -> tuple[list[dict], int, int]:
    """دریافت لیست تیکت‌ها با صفحه‌بندی برای پنل ادمین (مانند Senfi_bot)"""
    import math
    where_clauses = []
    params: list[Any] = []
    if category_id > 0:
        where_clauses.append("t.category_id = ?")
        params.append(category_id)
    if status and status != "همه":
        where_clauses.append("t.status = ?")
        params.append(status)

    where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    async with get_async_db() as db:
        count_cursor = await db.execute(f"SELECT COUNT(*) AS total FROM tickets t {where_str}", tuple(params))
        try:
            total_count = (await count_cursor.fetchone())["total"]
        finally:
            await count_cursor.close()

        total_pages = max(1, math.ceil(total_count / per_page))
        page = min(max(1, page), total_pages)
        offset = (page - 1) * per_page

        query = f"""
            SELECT t.*, c.title AS category_title
            FROM tickets t
            LEFT JOIN ticket_categories c ON t.category_id = c.id
            {where_str}
            ORDER BY t.id DESC
            LIMIT ? OFFSET ?
        """
        cursor = await db.execute(query, tuple(params + [per_page, offset]))
        try:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows], total_count, total_pages
        finally:
            await cursor.close()


async def get_ticket_status_counts() -> dict[str, int]:
    counts = {"خوانده نشده": 0, "پاسخ داده شده": 0, "همه": 0}
    async with get_async_db() as db:
        cursor = await db.execute("SELECT status, COUNT(*) AS cnt FROM tickets GROUP BY status")
        try:
            rows = await cursor.fetchall()
            total = 0
            for r in rows:
                counts[r["status"]] = r["cnt"]
                total += r["cnt"]
            counts["همه"] = total
            return counts
        finally:
            await cursor.close()


# =========================
# Polls & Surveys (سیستم نظرسنجی پیشرفته چندتایی)
# =========================

async def create_poll(question: str, options: list[str], title: str = "") -> int:
    import json
    opts_json = json.dumps(options, ensure_ascii=False)
    title = title or question[:30]
    async with get_async_db() as db:
        cursor = await db.execute("""
            INSERT INTO polls (title, question, options) VALUES (?, ?, ?)
        """, (title.strip(), question.strip(), opts_json))
        return cursor.lastrowid or 0


async def get_all_active_polls() -> list[dict]:
    import json
    rows = await _fetchall("SELECT * FROM polls WHERE is_active = 1 ORDER BY id DESC")
    res = []
    for r in rows:
        d = dict(r)
        d["options"] = json.loads(d["options"])
        res.append(d)
    return res


async def get_all_polls_admin() -> list[dict]:
    import json
    rows = await _fetchall("SELECT * FROM polls ORDER BY id DESC")
    res = []
    for r in rows:
        d = dict(r)
        d["options"] = json.loads(d["options"])
        res.append(d)
    return res


async def toggle_poll_status(poll_id: int) -> bool:
    async with get_async_db() as db:
        await db.execute("UPDATE polls SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?", (poll_id,))
    return True


async def delete_poll(poll_id: int) -> bool:
    async with get_async_db() as db:
        await db.execute("DELETE FROM poll_votes WHERE poll_id = ?", (poll_id,))
        await db.execute("DELETE FROM polls WHERE id = ?", (poll_id,))
    return True


async def get_active_poll() -> dict | None:
    import json
    row = await _fetchone("SELECT * FROM polls WHERE is_active = 1 ORDER BY id DESC LIMIT 1")
    if not row:
        return None
    d = dict(row)
    d["options"] = json.loads(d["options"])
    return d


async def get_poll(poll_id: int) -> dict | None:
    import json
    row = await _fetchone("SELECT * FROM polls WHERE id = ?", (poll_id,))
    if not row:
        return None
    d = dict(row)
    d["options"] = json.loads(d["options"])
    return d


async def record_poll_vote(poll_id: int, telegram_id: int, option_idx: int) -> bool:
    async with get_async_db() as db:
        try:
            await db.execute("""
                INSERT INTO poll_votes (poll_id, telegram_id, option_idx)
                VALUES (?, ?, ?)
                ON CONFLICT(poll_id, telegram_id) DO UPDATE SET option_idx = excluded.option_idx
            """, (poll_id, telegram_id, option_idx))
            return True
        except Exception:
            return False


async def get_user_poll_vote(poll_id: int, telegram_id: int) -> int | None:
    row = await _fetchone("""
        SELECT option_idx FROM poll_votes WHERE poll_id = ? AND telegram_id = ?
    """, (poll_id, telegram_id))
    return row["option_idx"] if row else None


async def get_poll_results(poll_id: int) -> dict:
    poll = await get_poll(poll_id)
    if not poll:
        return {}
    async with get_async_db() as db:
        cursor = await db.execute("""
            SELECT option_idx, COUNT(*) AS votes
            FROM poll_votes
            WHERE poll_id = ?
            GROUP BY option_idx
        """, (poll_id,))
        try:
            rows = await cursor.fetchall()
            votes_map = {r["option_idx"]: r["votes"] for r in rows}
            total_votes = sum(votes_map.values())
            res = []
            for idx, opt in enumerate(poll["options"]):
                cnt = votes_map.get(idx, 0)
                pct = round((cnt / total_votes * 100), 1) if total_votes > 0 else 0
                res.append({"option": opt, "votes": cnt, "percentage": pct})
            return {
                "poll_id": poll_id,
                "question": poll["question"],
                "total_votes": total_votes,
                "results": res
            }
        finally:
            await cursor.close()


async def close_active_poll() -> bool:
    async with get_async_db() as db:
        await db.execute("UPDATE polls SET is_active = 0 WHERE is_active = 1")
    return True

async def get_user_count() -> int:
    row = await _fetchone("SELECT COUNT(*) AS cnt FROM users")
    return int(row["cnt"]) if row else 0


async def get_active_user_count() -> int:
    """
    تعداد کاربرانی که حداقل bale_id یا bale_token تنظیم کرده‌اند (کاربر فعال)
    """
    row = await _fetchone("""
        SELECT COUNT(*) AS cnt FROM users
        WHERE bale_id IS NOT NULL
           OR (bale_token IS NOT NULL AND bale_token != '')
    """)
    return int(row["cnt"]) if row else 0


async def is_active_user(tg_id: int) -> bool:
    row = await _fetchone("""
        SELECT 1 FROM users
        WHERE telegram_id = ?
          AND (bale_id IS NOT NULL OR (bale_token IS NOT NULL AND bale_token != ''))
    """, (tg_id,))
    return row is not None



# =========================
# Whitelist (لیست سفید)
# =========================

def is_whitelist_enabled() -> bool:
    return _WHITELIST_ENABLED


async def set_whitelist_enabled(enabled: bool) -> bool:
    global _WHITELIST_ENABLED
    _WHITELIST_ENABLED = enabled
    await set_setting("whitelist_enabled", str(enabled).lower())
    if enabled:
        # درصورت فعال بودن whitelist باید ادمین به آن اضافه گردد
        admin_ids = set(_ADMIN_USERS).union(config.ADMIN_IDS)
        for admin_id in admin_ids:
            await add_to_whitelist(admin_id)
    return True


def is_user_whitelisted(tg_id: int) -> bool:
    if not _WHITELIST_ENABLED:
        return True
    if tg_id in _ADMIN_USERS or tg_id in config.ADMIN_IDS:
        return True
    return tg_id in _WHITELIST_USERS


async def add_to_whitelist(tg_id: int) -> bool:
    _WHITELIST_USERS.add(tg_id)
    async with get_async_db() as db:
        await db.execute("INSERT OR IGNORE INTO whitelist (telegram_id) VALUES (?)", (tg_id,))
    logger.info(f"[MODEL-ASYNC] User {tg_id} added to whitelist")
    return True


async def remove_from_whitelist(tg_id: int) -> bool:
    if _WHITELIST_ENABLED and (tg_id in _ADMIN_USERS or tg_id in config.ADMIN_IDS):
        logger.warning(f"[MODEL-ASYNC] Cannot remove admin {tg_id} from whitelist while whitelist is enabled.")
        return False
    _WHITELIST_USERS.discard(tg_id)
    async with get_async_db() as db:
        await db.execute("DELETE FROM whitelist WHERE telegram_id = ?", (tg_id,))
    logger.info(f"[MODEL-ASYNC] User {tg_id} removed from whitelist")
    return True


def get_whitelist_users() -> list[int]:
    return sorted(list(_WHITELIST_USERS))


# =========================
# Captcha Settings (تنظیمات کپچا)
# =========================

def is_captcha_ticket_enabled() -> bool:
    return _CAPTCHA_TICKET_ENABLED


async def set_captcha_ticket_enabled(enabled: bool) -> bool:
    global _CAPTCHA_TICKET_ENABLED
    _CAPTCHA_TICKET_ENABLED = enabled
    await set_setting("captcha_ticket_enabled", str(enabled).lower())
    return True


def is_captcha_poll_enabled() -> bool:
    return _CAPTCHA_POLL_ENABLED


async def set_captcha_poll_enabled(enabled: bool) -> bool:
    global _CAPTCHA_POLL_ENABLED
    _CAPTCHA_POLL_ENABLED = enabled
    await set_setting("captcha_poll_enabled", str(enabled).lower())
    return True


def is_captcha_file_enabled() -> bool:
    return _CAPTCHA_FILE_ENABLED


async def set_captcha_file_enabled(enabled: bool) -> bool:
    global _CAPTCHA_FILE_ENABLED
    _CAPTCHA_FILE_ENABLED = enabled
    await set_setting("captcha_file_enabled", str(enabled).lower())
    return True

