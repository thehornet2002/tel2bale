from typing import Any

from db.db_async import get_async_db, get_async_db_immediate
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

_LIMIT_VOLUME:float = 0

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

async def set_limit_volume(limit_volume:float):
    global _LIMIT_VOLUME
    _LIMIT_VOLUME = limit_volume
    return



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
    row = await _fetchone(
        "SELECT 1 FROM users WHERE telegram_id = ?",
        (tg_id,),
    )
    return row is not None


async def add_user(tg_id: int) -> bool:
    async with get_async_db() as db:
        cursor = await db.execute("""
            INSERT OR IGNORE INTO users (telegram_id, limit_download)
            VALUES (?,?)
        """, (tg_id, _LIMIT_VOLUME))
        try:
            added = cursor.rowcount > 0
        finally:
            await cursor.close()

    if added:
        logger.info(f"[MODEL-ASYNC] User added: {tg_id}")
    return added


async def check_admin(tg_id: int) -> bool:
    row = await _fetchone(
        """
        SELECT 1
        FROM users
        WHERE telegram_id = ?
          AND is_admin = 1
        """,
        (tg_id,),
    )
    return row is not None


async def check_ban(tg_id: int) -> bool:
    row = await _fetchone(
        """
        SELECT 1
        FROM users
        WHERE telegram_id = ?
          AND is_banned = 1
        """,
        (tg_id,),
    )
    return row is not None


# =========================
# State
# =========================

async def set_state(tg_id: int, state: str) -> bool:
    success = await _update_user_field(tg_id, "state", state)
    if success:
        logger.debug(f"[MODEL-ASYNC] State changed for user {tg_id}: {state}")
    return success


async def get_state(tg_id: int) -> str:
    return await _get_user_field(tg_id, "state", "home")


# =========================
# Bale ID
# =========================

async def get_bale_id(tg_id: int) -> int | None:
    return await _get_user_field(tg_id, "bale_id", None)


async def set_bale_id(tg_id: int, bale_id: int) -> bool:
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
    success = await _update_user_field(tg_id, "is_banned", 1)
    if success:
        logger.warning(f"[MODEL-ASYNC] User banned: {tg_id}")
    return success


async def unban_user(tg_id: int) -> bool:
    success = await _update_user_field(tg_id, "is_banned", 0)
    if success:
        logger.info(f"[MODEL-ASYNC] User unbanned: {tg_id}")
    return success


# =========================
# Admin
# =========================

async def set_admin(tg_id: int) -> bool:
    success = await _update_user_field(tg_id, "is_admin", 1)
    if success:
        logger.info(f"[MODEL-ASYNC] User promoted to admin: {tg_id}")
    return success


async def unset_admin(tg_id: int) -> bool:
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
    return await _get_user_field(tg_id, "bale_token", "")


async def set_bale_token(tg_id: int, bale_token: str) -> bool:
    return await _update_user_field(tg_id, "bale_token", bale_token)

async def get_s3_endpoint(tg_id: int) -> str | None:
    return await _get_user_field(tg_id, "s3_endpoint", None)


async def set_s3_endpoint(tg_id: int, s3_endpoint: str) -> bool:
    return await _update_user_field(tg_id, "s3_endpoint", s3_endpoint)

# =========================
# Support messages (پیام به پشتیبانی)
# =========================

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
    row = await _fetchone(
        """
        SELECT telegram_id FROM support_messages
        WHERE group_message_id = ? AND is_answered = 0
        """,
        (group_message_id,),
    )
    return row["telegram_id"] if row else None


async def mark_support_message_answered(group_message_id: int) -> bool:
    return await _execute(
        "UPDATE support_messages SET is_answered = 1 WHERE group_message_id = ?",
        (group_message_id,),
    )

# =========================
# User / active-user limits (MAX_USERS, MAX_ACTIVE_USERS)
# =========================

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
