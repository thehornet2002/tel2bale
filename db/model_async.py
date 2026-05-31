from db.db_async import get_async_db
from utils.logger import get_logger
from typing import Any
 
logger = get_logger(__name__)



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


async def _get_user_field(
    tg_id: int,
    field: str,
    default: Any = None
) -> Any:
    row = await _fetchone(
        f"SELECT {field} FROM users WHERE telegram_id = ?",
        (tg_id,)
    )

    if row is None:
        return default
    return row.get(field, default)






# =========================
# User existence / status
# =========================

async def is_user_exist(tg_id: int) -> bool:
    row = await _fetchone(
        "SELECT 1 FROM users WHERE telegram_id = ?",
        (tg_id,)
    )
    return row is not None



async def add_user(tg_id: int) -> bool:
    async with get_async_db() as db:
        cursor = await db.execute("""
            INSERT OR IGNORE INTO users (telegram_id)
            VALUES (?)
        """, (tg_id,))
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
        (tg_id,)
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
        (tg_id,)
    )
    return row is not None



# =========================
# State
# =========================


async def set_state(tg_id: int, state: str) -> bool:
    success = await _execute("""
        UPDATE users
        SET state = ?,
            updated_at = datetime('now','localtime')
        WHERE telegram_id = ?
    """, (state, tg_id))
    if success:
        logger.debug(
            f"[MODEL-ASYNC] State changed "
            f"for user {tg_id}: {state}"
        )
    return success


async def get_state(tg_id: int) -> str:
    return await _get_user_field(
        tg_id,
        "state",
        "home"
    )


# =========================
# Bale ID
# =========================

async def get_bale_id(
    tg_id: int
) -> int | None:

    return await _get_user_field(
        tg_id,
        "bale_id",
        None
    )


async def set_bale_id(
    tg_id: int,
    bale_id: int
) -> bool:

    success = await _execute("""
        UPDATE users
        SET bale_id = ?,
            updated_at = datetime('now','localtime')
        WHERE telegram_id = ?
    """, (bale_id, tg_id))

    if success:
        logger.debug(
            f"[MODEL-ASYNC] Bale ID updated "
            f"for user {tg_id}"
        )

    return success


async def get_telegram_ids_by_bale_id(
    bale_id: int
) -> list[int]:

    rows = await _fetchall("""
        SELECT telegram_id
        FROM users
        WHERE bale_id = ?
    """, (bale_id,))

    return [
        row["telegram_id"]
        for row in rows
    ]


# =========================
# Download limits
# =========================

async def get_downloaded_volume(
    tg_id: int
) -> float:

    return float(
        await _get_user_field(
            tg_id,
            "downloaded_volume",
            0.0
        )
    )


async def set_downloaded_volume(
    tg_id: int,
    volume: float
) -> bool:

    return await _execute("""
        UPDATE users
        SET downloaded_volume = ?,
            updated_at = datetime('now','localtime')
        WHERE telegram_id = ?
    """, (volume, tg_id))


async def get_limit_download(
    tg_id: int
) -> float:

    return float(
        await _get_user_field(
            tg_id,
            "limit_download",
            0.0
        )
    )


async def set_limit_download(
    tg_id: int,
    limit: float
) -> bool:

    success = await _execute("""
        UPDATE users
        SET limit_download = ?,
            updated_at = datetime('now','localtime')
        WHERE telegram_id = ?
    """, (limit, tg_id))

    if success:
        logger.debug(
            f"[MODEL-ASYNC] Download limit "
            f"updated for user {tg_id}"
        )

    return success


async def set_limit_download_all(
    limit: float
) -> None:

    async with get_async_db() as db:
        await db.execute("""
            UPDATE users
            SET limit_download = ?,
                updated_at = datetime('now','localtime')
        """, (limit,))

    logger.info(
        f"[MODEL-ASYNC] Global download limit "
        f"set to {limit}"
    )

# =========================
# Ban / Unban
# =========================
async def ban_user(tg_id: int) -> bool:
    success = await _execute("""
        UPDATE users
        SET is_banned = 1,
            updated_at = datetime('now','localtime')
        WHERE telegram_id = ?
    """, (tg_id,))

    if success:
        logger.warning(
            f"[MODEL-ASYNC] User banned: {tg_id}"
        )

    return success


async def unban_user(tg_id: int) -> bool:
    success = await _execute("""
        UPDATE users
        SET is_banned = 0,
            updated_at = datetime('now','localtime')
        WHERE telegram_id = ?
    """, (tg_id,))

    if success:
        logger.info(
            f"[MODEL-ASYNC] User unbanned: {tg_id}"
        )

    return success


# =========================
# Admin
# =========================

async def set_admin(tg_id: int) -> bool:
    success = await _execute("""
        UPDATE users
        SET is_admin = 1,
            updated_at = datetime('now','localtime')
        WHERE telegram_id = ?
    """, (tg_id,))

    if success:
        logger.info(
            f"[MODEL-ASYNC] User promoted to admin: {tg_id}"
        )

    return success


async def unset_admin(tg_id: int) -> bool:
    success = await _execute("""
        UPDATE users
        SET is_admin = 0,
            updated_at = datetime('now','localtime')
        WHERE telegram_id = ?
    """, (tg_id,))

    if success:
        logger.info(
            f"[MODEL-ASYNC] Admin removed: {tg_id}"
        )

    return success

# =========================
# Statistics
# =========================

async def get_top_users(
    limit: int = 10
) -> list[dict]:

    rows = await _fetchall("""
        SELECT
            telegram_id,
            bale_id,
            downloaded_volume
        FROM users
        ORDER BY downloaded_volume DESC
        LIMIT ?
    """, (limit,))

    return [
        {
            "tg_id": row["telegram_id"],
            "bale_id": row["bale_id"],
            "downloaded_volume": round(
                float(row["downloaded_volume"]),
                2
            )
        }
        for row in rows
    ]


async def get_all_telegram_ids() -> list[int]:
    rows = await _fetchall("""
        SELECT telegram_id
        FROM users
    """)

    return [
        row["telegram_id"]
        for row in rows
    ]

# =========================
# Support Messages
# =========================

async def save_support_message(
    tg_id: int,
    message_text: str
) -> None:

    async with get_async_db() as db:
        await db.execute("""
            INSERT INTO support_messages (
                telegram_id,
                message_text
            )
            VALUES (?, ?)
        """, (tg_id, message_text))

    logger.info(
        f"[MODEL-ASYNC] Support message saved "
        f"from user {tg_id}"
    )


async def get_unread_support_message() -> dict | None:
    """
    دریافت یک پیام خوانده‌نشده و
    علامت‌گذاری آن به عنوان خوانده‌شده.

    در برابر race condition مقاوم‌تر
    از نسخه قبلی است.
    """

    async with get_async_db() as db:

        await db.execute("BEGIN IMMEDIATE")

        cursor = await db.execute("""
            SELECT
                id,
                telegram_id,
                message_text
            FROM support_messages
            WHERE is_read = 0
            ORDER BY sent_at ASC
            LIMIT 1
        """)

        try:
            row = await cursor.fetchone()
        finally:
            await cursor.close()

        if row is None:
            return None

        await db.execute("""
            UPDATE support_messages
            SET is_read = 1
            WHERE id = ?
        """, (row["id"],))

        return {
            "tg_id": row["telegram_id"],
            "message_text": row["message_text"]
        }


async def get_unread_support_count() -> int:
    row = await _fetchone("""
        SELECT COUNT(*) AS total
        FROM support_messages
        WHERE is_read = 0
    """)

    if row is None:
        return 0

    return int(row["total"])


async def get_support_messages(
    limit: int = 50
) -> list[dict]:

    rows = await _fetchall("""
        SELECT
            id,
            telegram_id,
            message_text,
            is_read,
            sent_at
        FROM support_messages
        ORDER BY sent_at DESC
        LIMIT ?
    """, (limit,))

    return rows


async def mark_support_message_read(
    message_id: int
) -> bool:

    return await _execute("""
        UPDATE support_messages
        SET is_read = 1
        WHERE id = ?
    """, (message_id,))


async def delete_support_message(
    message_id: int
) -> bool:

    return await _execute("""
        DELETE FROM support_messages
        WHERE id = ?
    """, (message_id,))

##########################
#### Arvan Storage
##########################

async def get_access_key(
    tg_id: int
) -> str | None:

    return await _get_user_field(
        tg_id,
        "access_key",
        None
    )


async def set_access_key(
    tg_id: int,
    access_key: str
) -> bool:

    return await _execute("""
        UPDATE users
        SET access_key = ?,
            updated_at = datetime('now','localtime')
        WHERE telegram_id = ?
    """, (
        access_key,
        tg_id
    ))


async def get_secret_key(
    tg_id: int
) -> str | None:

    return await _get_user_field(
        tg_id,
        "secret_key",
        None
    )


async def set_secret_key(
    tg_id: int,
    secret_key: str
) -> bool:

    return await _execute("""
        UPDATE users
        SET secret_key = ?,
            updated_at = datetime('now','localtime')
        WHERE telegram_id = ?
    """, (
        secret_key,
        tg_id
    ))


async def get_bale_token(
    tg_id: int
) -> str:

    return await _get_user_field(
        tg_id,
        "bale_token",
        ""
    )


async def set_bale_token(
    tg_id: int,
    bale_token: str
) -> bool:

    return await _execute("""
        UPDATE users
        SET bale_token = ?,
            updated_at = datetime('now','localtime')
        WHERE telegram_id = ?
    """, (
        bale_token,
        tg_id
    ))