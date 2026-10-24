import os
from typing import Any

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

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
# Every field placed inside SQL strings must be verified in these frozensets
# to guarantee protection against SQL injection.
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
_WHITELIST_USERS: set[int] = set()
_WHITELIST_ENABLED: bool = False
_CAPTCHA_TICKET_ENABLED: bool = True
_CAPTCHA_POLL_ENABLED: bool = False
_CAPTCHA_FILE_ENABLED: bool = False
_CAPTCHA_DOWNLOAD_ENABLED: bool = False
_CAPTCHA_DIFFICULTY: int = 3
_CAPTCHA_LENGTH: int = 5

# =========================
# Tables & Settings
# =========================

async def create_tables() -> None:
    """Create all required database tables if they do not exist."""
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

        # Ticket categories table
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

        # Support tickets table
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

        # Insert default ticket categories if empty
        cursor = await db.execute("SELECT COUNT(*) AS cnt FROM ticket_categories")
        cat_cnt = (await cursor.fetchone())["cnt"]
        if cat_cnt == 0:
            defaults = ["پشتیبانی عمومی", "مشکلات فنی و اتصال", "پیشنهادات و انتقادات"]
            for title in defaults:
                await db.execute("INSERT OR IGNORE INTO ticket_categories (title) VALUES (?)", (title,))

        # Multi-polls table
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

        # Poll votes table with foreign key cascade
        await db.execute("""
            CREATE TABLE IF NOT EXISTS poll_votes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id     INTEGER NOT NULL,
                telegram_id INTEGER NOT NULL,
                option_idx  INTEGER NOT NULL,
                created_at  TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(poll_id, telegram_id),
                FOREIGN KEY (poll_id) REFERENCES polls (id) ON DELETE CASCADE
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_poll_votes ON poll_votes (poll_id, telegram_id)")

        # Verify foreign key constraint on poll_votes for legacy databases
        fk_cursor = await db.execute("PRAGMA foreign_key_list(poll_votes)")
        try:
            fk_rows = await fk_cursor.fetchall()
            if not fk_rows:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS poll_votes_new (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        poll_id     INTEGER NOT NULL,
                        telegram_id INTEGER NOT NULL,
                        option_idx  INTEGER NOT NULL,
                        created_at  TEXT DEFAULT (datetime('now','localtime')),
                        UNIQUE(poll_id, telegram_id),
                        FOREIGN KEY (poll_id) REFERENCES polls (id) ON DELETE CASCADE
                    )
                """)
                await db.execute("INSERT OR IGNORE INTO poll_votes_new SELECT * FROM poll_votes")
                await db.execute("DROP TABLE poll_votes")
                await db.execute("ALTER TABLE poll_votes_new RENAME TO poll_votes")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_poll_votes ON poll_votes (poll_id, telegram_id)")
        except Exception:
            pass
        finally:
            await fk_cursor.close()

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

        await db.execute("""
            CREATE TABLE IF NOT EXISTS download_reservations (
                reservation_id TEXT PRIMARY KEY,
                telegram_id    INTEGER NOT NULL,
                size_bytes     INTEGER NOT NULL,
                status         TEXT NOT NULL,
                created_at     TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_res_user ON download_reservations (telegram_id)")

    await init_cache()
    await migrate_legacy_credentials()
    await init_redis(config.REDIS_URL)
    logger.info("[MODEL-ASYNC] Database tables, cache, and credential migrations initialized successfully")


async def init_cache() -> None:
    """Load frequently accessed data into RAM cache to maximize performance."""
    global _WHITELIST_ENABLED, _LIMIT_VOLUME
    _EXISTING_USERS.clear()
    _ADMIN_USERS.clear()
    _BANNED_USERS.clear()
    _STATE_CACHE.clear()
    _BALE_ID_CACHE.clear()
    _WHITELIST_USERS.clear()

    async with get_async_db() as db:
        cursor = await db.execute("SELECT telegram_id, is_admin, is_banned, state, bale_id FROM users")
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

    global _CAPTCHA_TICKET_ENABLED, _CAPTCHA_POLL_ENABLED, _CAPTCHA_FILE_ENABLED, _CAPTCHA_DOWNLOAD_ENABLED, _CAPTCHA_DIFFICULTY, _CAPTCHA_LENGTH
    saved_ct = await get_setting("captcha_ticket_enabled", "true")
    _CAPTCHA_TICKET_ENABLED = (saved_ct.lower() == "true")
    saved_cp = await get_setting("captcha_poll_enabled", "false")
    _CAPTCHA_POLL_ENABLED = (saved_cp.lower() == "true")
    saved_cf = await get_setting("captcha_file_enabled", "false")
    _CAPTCHA_FILE_ENABLED = (saved_cf.lower() == "true")
    saved_cd = await get_setting("captcha_download_enabled", "false")
    _CAPTCHA_DOWNLOAD_ENABLED = (saved_cd.lower() == "true")

    saved_diff = await get_setting("captcha_difficulty", "3")
    try:
        _CAPTCHA_DIFFICULTY = max(1, min(5, int(saved_diff)))
    except ValueError:
        _CAPTCHA_DIFFICULTY = 3

    saved_len = await get_setting("captcha_length", "5")
    try:
        _CAPTCHA_LENGTH = max(4, min(10, int(saved_len)))
    except ValueError:
        _CAPTCHA_LENGTH = 5

    # Load dynamic runtime settings into config
    saved_donation = await get_setting("donation_link", "")
    if saved_donation:
        config.DONATION_LINK = saved_donation

    saved_max_u = await get_setting("max_users", "")
    if saved_max_u:
        try:
            config.MAX_USERS = int(saved_max_u)
        except ValueError:
            pass

    saved_max_au = await get_setting("max_active_users", "")
    if saved_max_au:
        try:
            config.MAX_ACTIVE_USERS = int(saved_max_au)
        except ValueError:
            pass

    saved_channels = await get_setting("ads_channels", "")
    if saved_channels:
        config.ADS_CHANNELS = [c.strip() for c in saved_channels.split(",") if c.strip()]


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
    # Save to Redis first if available
    if is_redis_available():
        await redis_set_state(tg_id, state)

    success = await _update_user_field(tg_id, "state", state)
    if success:
        logger.debug(f"[MODEL-ASYNC] State changed for user {tg_id}: {state}")
    return success


async def get_state(tg_id: int) -> str:
    # 1. Check Redis first
    if is_redis_available():
        r_state = await redis_get_state(tg_id)
        if r_state is not None:
            _STATE_CACHE[tg_id] = r_state
            return r_state

    # 2. Check in-memory RAM cache
    if tg_id in _STATE_CACHE:
        return _STATE_CACHE[tg_id]

    # 3. Fallback to SQLite persistent database
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

async def reserve_download_quota(tg_id: int, file_size_bytes: int | None, reservation_id: str | None = None) -> bool:
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
        if reservation_id:
            res_cur = await db.execute("""
                SELECT status FROM download_reservations WHERE reservation_id = ?
            """, (reservation_id,))
            try:
                res_row = await res_cur.fetchone()
                if res_row is not None:
                    # Idempotency check: if already reserved, return True without double-incrementing
                    return res_row["status"] == "reserved"
            finally:
                await res_cur.close()

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

        if reservation_id:
            await db.execute("""
                INSERT INTO download_reservations (reservation_id, telegram_id, size_bytes, status)
                VALUES (?, ?, ?, 'reserved')
            """, (reservation_id, tg_id, file_size_bytes))

        logger.debug(
            f"[MODEL-ASYNC] Quota reserved for user {tg_id}: "
            f"{new_downloaded_volume:.6f}GB"
        )
        return True


async def release_download_quota(tg_id: int, file_size_bytes: int | None = None, reservation_id: str | None = None) -> bool:
    """
    Atomically rolls back a previously reserved quota amount with idempotency guarantees.
    Strictly verifies ownership (telegram_id matches reservation) and uses exact reserved size_bytes.
    """
    async with get_async_db_immediate() as db:
        actual_bytes = file_size_bytes or 0
        if reservation_id:
            res_cur = await db.execute("""
                SELECT size_bytes, status, telegram_id
                FROM download_reservations
                WHERE reservation_id = ?
            """, (reservation_id,))
            try:
                res_row = await res_cur.fetchone()
                if not res_row:
                    return False
                if res_row["telegram_id"] != tg_id:
                    logger.warning(f"[MODEL-ASYNC] Quota release rejected: reservation owner mismatch ({res_row['telegram_id']} != {tg_id})")
                    return False
                if res_row["status"] != "reserved":
                    # Already committed or rolled back; idempotent no-op
                    return True
                actual_bytes = res_row["size_bytes"]
            finally:
                await res_cur.close()

            cursor = await db.execute("""
                UPDATE download_reservations
                SET status = 'rolled_back'
                WHERE reservation_id = ? AND telegram_id = ? AND status = 'reserved'
            """, (reservation_id, tg_id))
            if cursor.rowcount == 0:
                return True

        if actual_bytes <= 0:
            return True

        file_size_gb = actual_bytes / (1024 ** 3)
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


async def commit_download_quota(reservation_id: str | None, tg_id: int | None = None) -> bool:
    """Commit quota reservation so it can no longer be rolled back."""
    if not reservation_id:
        return True
    async with get_async_db() as db:
        if tg_id:
            cursor = await db.execute("""
                UPDATE download_reservations
                SET status = 'committed'
                WHERE reservation_id = ? AND telegram_id = ? AND status = 'reserved'
            """, (reservation_id, tg_id))
        else:
            cursor = await db.execute("""
                UPDATE download_reservations
                SET status = 'committed'
                WHERE reservation_id = ? AND status = 'reserved'
            """, (reservation_id,))
        return cursor.rowcount == 1


async def cleanup_stale_reservations(max_age_hours: int = 24) -> int:
    """
    Purge old quota reservation records older than max_age_hours.
    Strictly refunds any uncommitted 'reserved' records before deleting them.
    """
    async with get_async_db_immediate() as db:
        # 1. Find all stale reservations still in 'reserved' state to refund user quota
        cur = await db.execute("""
            SELECT reservation_id, telegram_id, size_bytes
            FROM download_reservations
            WHERE status = 'reserved' AND created_at < datetime('now', '-' || ? || ' hours')
        """, (max_age_hours,))
        try:
            stale_reserved = await cur.fetchall()
            for r in stale_reserved:
                res_id = r["reservation_id"]
                u_id = r["telegram_id"]
                s_bytes = r["size_bytes"]
                s_gb = s_bytes / (1024 ** 3)
                await db.execute("""
                    UPDATE users
                    SET downloaded_volume = MAX(0.0, downloaded_volume - ?),
                        updated_at = datetime('now','localtime')
                    WHERE telegram_id = ?
                """, (s_gb, u_id))
                await db.execute("""
                    UPDATE download_reservations
                    SET status = 'rolled_back'
                    WHERE reservation_id = ?
                """, (res_id,))
                logger.info(f"[MODEL-ASYNC] Refunded stale reservation {res_id} ({s_gb:.4f} GB) to user {u_id}")
        finally:
            await cur.close()

        # 2. Delete all records older than max_age_hours
        cursor = await db.execute("""
            DELETE FROM download_reservations
            WHERE created_at < datetime('now', '-' || ? || ' hours')
        """, (max_age_hours,))
        deleted = cursor.rowcount
        if deleted > 0:
            logger.info(f"[MODEL-ASYNC] Purged {deleted} stale download reservation records")
        return deleted


async def set_limit_download_all(limit: float) -> None:
    # Update all users globally (without WHERE clause)
    async with get_async_db() as db:
        await db.execute("""
            UPDATE users
            SET limit_download = ?,
                updated_at = datetime('now','localtime')
        """, (limit,))

    logger.info(f"[MODEL-ASYNC] Global download limit set to {limit}")


async def get_user_quota_info(tg_id: int) -> dict:
    """Retrieve detailed download quota consumption and remaining limit."""
    async with get_async_db() as db:
        cursor = await db.execute("""
            SELECT downloaded_volume, limit_download
            FROM users
            WHERE telegram_id = ?
        """, (tg_id,))
        try:
            row = await cursor.fetchone()
        finally:
            await cursor.close()

        if not row:
            return {
                "downloaded_gb": 0.0,
                "downloaded_mb": 0.0,
                "limit_gb": 0.0,
                "remaining_gb": 0.0,
                "remaining_mb": 0.0,
                "is_unlimited": True,
            }

        downloaded = float(row["downloaded_volume"] or 0.0)
        limit = float(row["limit_download"] or 0.0)
        is_unlimited = (limit <= 0)
        remaining = 0.0 if is_unlimited else max(0.0, limit - downloaded)

        return {
            "downloaded_gb": downloaded,
            "downloaded_mb": downloaded * 1024,
            "limit_gb": limit,
            "remaining_gb": remaining,
            "remaining_mb": remaining * 1024,
            "is_unlimited": is_unlimited,
        }


async def reset_user_download_quota(tg_id: int) -> bool:
    """Reset downloaded volume to 0 for a user."""
    return await _update_user_field(tg_id, "downloaded_volume", 0.0)


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
# Symmetric Encryption for Stored Sensitive Credentials
# =========================

_ENC_PREFIX = "enc:gcm:v2:"


def _get_encryption_key(salt: bytes) -> bytes:
    """
    Derive a 256-bit AES key using PBKDF2 with 100,000 iterations and per-record salt.
    Enforces strictly fail-closed: requires ENCRYPTION_KEY without any fallback.
    """
    if not HAS_CRYPTOGRAPHY:
        raise RuntimeError("The 'cryptography' package is required for secure credential encryption.")

    seed = (
        getattr(config, "ENCRYPTION_KEY", None)
        or os.getenv("ENCRYPTION_KEY")
        or ""
    ).strip()
    if not seed:
        raise RuntimeError("ENCRYPTION_KEY is required and must be configured in environment or .env.")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return kdf.derive(seed.encode("utf-8"))


def encrypt_credential(value: str | None) -> str | None:
    """
    Fail-closed AES-256-GCM encryption with per-record random 16-byte salt and 12-byte nonce.
    Never falls back to plaintext.
    """
    if not value or not isinstance(value, str):
        return value
    if value.startswith(_ENC_PREFIX):
        return value

    salt = os.urandom(16)
    key = _get_encryption_key(salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, value.encode("utf-8"), None)
    import base64
    payload = salt + nonce + ct
    encoded = base64.b64encode(payload).decode("ascii")
    return f"{_ENC_PREFIX}{encoded}"


def decrypt_credential(value: str | None) -> str | None:
    """Decrypt stored credential. Supports v2 (random salt) and legacy enc:gcm: format."""
    if not value or not isinstance(value, str):
        return value

    import base64
    if value.startswith(_ENC_PREFIX):
        raw = base64.b64decode(value[len(_ENC_PREFIX):])
        salt = raw[:16]
        nonce = raw[16:28]
        ct = raw[28:]
        key = _get_encryption_key(salt)
        aesgcm = AESGCM(key)
        decrypted = aesgcm.decrypt(nonce, ct, None)
        return decrypted.decode("utf-8")
    elif value.startswith("enc:gcm:"):
        legacy_prefix = "enc:gcm:"
        raw = base64.b64decode(value[len(legacy_prefix):])
        nonce = raw[:12]
        ct = raw[12:]
        legacy_salt = b"tel2bale_storage_salt_v1"
        key = _get_encryption_key(legacy_salt)
        aesgcm = AESGCM(key)
        decrypted = aesgcm.decrypt(nonce, ct, None)
        return decrypted.decode("utf-8")

    # Plaintext record (unmigrated)
    return value


async def migrate_legacy_credentials() -> None:
    """
    One-time startup migration: Encrypts any existing plaintext credentials in database.
    """
    async with get_async_db() as db:
        cursor = await db.execute("SELECT telegram_id, bale_token, access_key, secret_key FROM users")
        try:
            rows = await cursor.fetchall()
            for r in rows:
                t_id = r["telegram_id"]
                updates = {}
                for field in ("bale_token", "access_key", "secret_key"):
                    raw_val = r[field]
                    if raw_val and not raw_val.startswith("enc:gcm:"):
                        updates[field] = encrypt_credential(raw_val)

                if updates:
                    set_clauses = ", ".join(f"{f} = ?" for f in updates.keys())
                    vals = list(updates.values()) + [t_id]
                    await db.execute(f"UPDATE users SET {set_clauses} WHERE telegram_id = ?", tuple(vals))
                    logger.info(f"[CRYPTO-MIGRATION] Encrypted plaintext credentials for user {t_id}")
        finally:
            await cursor.close()

        # Post-migration verification: Ensure zero plaintext credentials remain
        check_cursor = await db.execute("""
            SELECT COUNT(*) AS cnt FROM users 
            WHERE (bale_token IS NOT NULL AND bale_token != '' AND NOT bale_token LIKE 'enc:gcm:%')
               OR (access_key IS NOT NULL AND access_key != '' AND NOT access_key LIKE 'enc:gcm:%')
               OR (secret_key IS NOT NULL AND secret_key != '' AND NOT secret_key LIKE 'enc:gcm:%')
        """)
        try:
            row = await check_cursor.fetchone()
            unmigrated = row["cnt"] if row else 0
            if unmigrated > 0:
                raise RuntimeError(f"Credential migration verification failed: {unmigrated} plaintext records remain.")
        finally:
            await check_cursor.close()


# =========================
# Arvan Storage credentials
# =========================

async def get_access_key(tg_id: int) -> str | None:
    val = await _get_user_field(tg_id, "access_key", None)
    return decrypt_credential(val)


async def set_access_key(tg_id: int, access_key: str) -> bool:
    enc_val = encrypt_credential(access_key)
    return await _update_user_field(tg_id, "access_key", enc_val)


async def get_secret_key(tg_id: int) -> str | None:
    val = await _get_user_field(tg_id, "secret_key", None)
    return decrypt_credential(val)


async def set_secret_key(tg_id: int, secret_key: str) -> bool:
    enc_val = encrypt_credential(secret_key)
    return await _update_user_field(tg_id, "secret_key", enc_val)


async def get_bale_token(tg_id: int) -> str:
    # Strictly read from storage with decryption; never retain raw plaintext in global static cache
    val = await _get_user_field(tg_id, "bale_token", "") or ""
    return decrypt_credential(val) or ""


async def set_bale_token(tg_id: int, bale_token: str) -> bool:
    enc_val = encrypt_credential(bale_token)
    return await _update_user_field(tg_id, "bale_token", enc_val)


async def get_s3_endpoint(tg_id: int) -> str | None:
    return await _get_user_field(tg_id, "s3_endpoint", None)


async def set_s3_endpoint(tg_id: int, s3_endpoint: str) -> bool:
    return await _update_user_field(tg_id, "s3_endpoint", s3_endpoint)

# =========================
# Support & Ticket System
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
    # Strict length sanitization on ticket inputs
    safe_subject = (subject or "پشتیبانی").strip()[:80]
    safe_message = (message or "").strip()[:4000]
    safe_user_name = (user_name or "کاربر").strip()[:60]

    async with get_async_db() as db:
        cursor = await db.execute("""
            INSERT INTO tickets (telegram_id, user_name, category_id, subject, message, status, is_anonymous, group_message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (telegram_id, safe_user_name, category_id, safe_subject, safe_message, STATUS_UNREAD, is_anonymous, group_message_id))
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


async def increment_support_message_count_atomic(tg_id: int, limit: int) -> bool:
    """
    Atomically increment support message count only if strictly below limit.
    Prevents race condition where concurrent messages bypass pending ticket limits.
    """
    if limit <= 0:
        return True

    async with get_async_db() as db:
        cursor = await db.execute("""
            UPDATE users
            SET support_message_count = support_message_count + 1,
                updated_at = datetime('now','localtime')
            WHERE telegram_id = ? AND support_message_count < ?
        """, (tg_id, limit))
        return cursor.rowcount > 0


async def decrement_support_message_count(tg_id: int) -> bool:
    """Safely decrement support message count on ticket creation failure."""
    return await _execute("""
        UPDATE users
        SET support_message_count = MAX(0, support_message_count - 1),
            updated_at = datetime('now','localtime')
        WHERE telegram_id = ?
    """, (tg_id,))


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
    """Save forwarded support message ID for response mapping."""
    async with get_async_db() as db:
        await db.execute("""
            INSERT INTO support_messages (telegram_id, group_message_id)
            VALUES (?, ?)
        """, (tg_id, group_message_id))
    return True


async def get_telegram_id_by_group_message(group_message_id: int) -> int | None:
    # Check tickets table first
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
    """Fetch paginated tickets list for administration panel."""
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
# Polls & Surveys
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
    """Validate that poll exists, is active, and option index is within bounds transactionally."""
    import json
    async with get_async_db() as db:
        try:
            cursor = await db.execute("SELECT options, is_active FROM polls WHERE id = ?", (poll_id,))
            row = await cursor.fetchone()
            if not row or not row["is_active"]:
                logger.warning(f"[POLL] Attempted vote on inactive or non-existent poll {poll_id}")
                return False

            options = json.loads(row["options"])
            if not isinstance(options, list) or not (0 <= option_idx < len(options)):
                logger.warning(f"[POLL] Invalid option index {option_idx} for poll {poll_id}")
                return False

            await db.execute("""
                INSERT INTO poll_votes (poll_id, telegram_id, option_idx)
                VALUES (?, ?, ?)
                ON CONFLICT(poll_id, telegram_id) DO UPDATE SET option_idx = excluded.option_idx
            """, (poll_id, telegram_id, option_idx))
            return True
        except Exception as e:
            logger.error(f"[POLL] Error recording vote: {e}")
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
# Whitelist System
# =========================

def is_whitelist_enabled() -> bool:
    return _WHITELIST_ENABLED


async def set_whitelist_enabled(enabled: bool) -> bool:
    global _WHITELIST_ENABLED
    _WHITELIST_ENABLED = enabled
    await set_setting("whitelist_enabled", str(enabled).lower())
    if enabled:
        # When whitelist is enabled, ensure administrators are included
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
# Captcha Settings
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


def is_captcha_download_enabled() -> bool:
    return _CAPTCHA_DOWNLOAD_ENABLED


async def set_captcha_download_enabled(enabled: bool) -> bool:
    global _CAPTCHA_DOWNLOAD_ENABLED
    _CAPTCHA_DOWNLOAD_ENABLED = enabled
    await set_setting("captcha_download_enabled", str(enabled).lower())
    return True


def get_captcha_difficulty() -> int:
    return _CAPTCHA_DIFFICULTY


async def set_captcha_difficulty(difficulty: int) -> bool:
    global _CAPTCHA_DIFFICULTY
    _CAPTCHA_DIFFICULTY = max(1, min(5, int(difficulty)))
    await set_setting("captcha_difficulty", str(_CAPTCHA_DIFFICULTY))
    return True


def get_captcha_length() -> int:
    return _CAPTCHA_LENGTH


async def set_captcha_length(length: int) -> bool:
    global _CAPTCHA_LENGTH
    _CAPTCHA_LENGTH = max(4, min(10, int(length)))
    await set_setting("captcha_length", str(_CAPTCHA_LENGTH))
    return True



