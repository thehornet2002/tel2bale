"""
Cookie management service for yt-dlp and media downloaders.
Supports global cookies (admin) and per-user custom cookies (Netscape format).
"""
import os
import time
from utils.logger import get_logger

logger = get_logger(__name__)

COOKIES_DIR = "cookies"
GLOBAL_COOKIE_FILE = os.path.join(COOKIES_DIR, "global_cookies.txt")
ROOT_COOKIE_FILE = "cookies.txt"


def ensure_cookies_dir() -> None:
    """Ensure the cookies directory exists."""
    os.makedirs(COOKIES_DIR, exist_ok=True)


def get_user_cookie_path(user_id: int) -> str:
    """Return file path for a specific user's cookie file."""
    ensure_cookies_dir()
    return os.path.join(COOKIES_DIR, f"user_{user_id}.txt")


def get_effective_cookie_file(user_id: int | None = None) -> str | None:
    """
    Resolve the active cookie file path:
    1. User-specific cookie file if exists and non-empty.
    2. Global cookies in cookies/global_cookies.txt.
    3. Root cookies.txt if present.
    """
    if user_id:
        user_path = get_user_cookie_path(user_id)
        if os.path.exists(user_path) and os.path.getsize(user_path) > 0:
            return user_path

    if os.path.exists(GLOBAL_COOKIE_FILE) and os.path.getsize(GLOBAL_COOKIE_FILE) > 0:
        return GLOBAL_COOKIE_FILE

    if os.path.exists(ROOT_COOKIE_FILE) and os.path.getsize(ROOT_COOKIE_FILE) > 0:
        return ROOT_COOKIE_FILE

    return None


def save_cookie_file(content: str | bytes, user_id: int | None = None) -> bool:
    """
    Save cookie content (Netscape cookies.txt format) globally or for a specific user.
    """
    try:
        ensure_cookies_dir()
        target_path = get_user_cookie_path(user_id) if user_id else GLOBAL_COOKIE_FILE

        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = content

        with open(target_path, "wb") as f:
            f.write(content_bytes)

        # If saving global cookies, keep root cookies.txt in sync
        if not user_id:
            try:
                with open(ROOT_COOKIE_FILE, "wb") as f:
                    f.write(content_bytes)
            except Exception:
                pass

        logger.info(f"[COOKIES] Saved cookie file ({len(content_bytes)} bytes) at {target_path}")
        return True
    except Exception as e:
        logger.error(f"[COOKIES] Failed to save cookie file: {e}")
        return False


def delete_cookie_file(user_id: int | None = None) -> bool:
    """Delete cookie file for user or globally."""
    try:
        target_path = get_user_cookie_path(user_id) if user_id else GLOBAL_COOKIE_FILE
        deleted = False

        if os.path.exists(target_path):
            os.remove(target_path)
            deleted = True

        if not user_id and os.path.exists(ROOT_COOKIE_FILE):
            try:
                os.remove(ROOT_COOKIE_FILE)
            except Exception:
                pass

        logger.info(f"[COOKIES] Deleted cookie file for user={user_id}")
        return deleted
    except Exception as e:
        logger.error(f"[COOKIES] Failed to delete cookie file: {e}")
        return False


def get_cookie_status(user_id: int | None = None) -> dict:
    """Return status dictionary about configured cookies."""
    path = get_effective_cookie_file(user_id)
    if not path or not os.path.exists(path):
        return {
            "has_cookie": False,
            "size_bytes": 0,
            "path": None,
            "is_user_specific": False,
        }

    size = os.path.getsize(path)
    is_user = user_id is not None and path == get_user_cookie_path(user_id)
    return {
        "has_cookie": size > 0,
        "size_bytes": size,
        "path": path,
        "is_user_specific": is_user,
    }
