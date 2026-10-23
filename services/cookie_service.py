"""
Cookie management service for yt-dlp and media downloaders.
Globally configured and managed exclusively by administrators (Netscape cookies.txt format).
"""
import os
from utils.logger import get_logger

logger = get_logger(__name__)

COOKIES_DIR = "cookies"
GLOBAL_COOKIE_FILE = os.path.join(COOKIES_DIR, "global_cookies.txt")
ROOT_COOKIE_FILE = "cookies.txt"


def ensure_cookies_dir() -> None:
    """Ensure the cookies directory exists."""
    os.makedirs(COOKIES_DIR, exist_ok=True)


def get_effective_cookie_file(user_id: int | None = None) -> str | None:
    """
    Resolve active global cookie file path configured by administrator:
    1. Global cookies in cookies/global_cookies.txt.
    2. Root cookies.txt if present.
    """
    if os.path.exists(GLOBAL_COOKIE_FILE) and os.path.getsize(GLOBAL_COOKIE_FILE) > 0:
        return GLOBAL_COOKIE_FILE

    if os.path.exists(ROOT_COOKIE_FILE) and os.path.getsize(ROOT_COOKIE_FILE) > 0:
        return ROOT_COOKIE_FILE

    return None


def save_cookie_file(content: str | bytes, user_id: int | None = None) -> bool:
    """
    Save global cookie content (Netscape cookies.txt format) by administrator.
    """
    try:
        ensure_cookies_dir()
        target_path = GLOBAL_COOKIE_FILE

        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = content

        with open(target_path, "wb") as f:
            f.write(content_bytes)

        try:
            with open(ROOT_COOKIE_FILE, "wb") as f:
                f.write(content_bytes)
        except Exception:
            pass

        logger.info(f"[COOKIES] Saved global cookie file ({len(content_bytes)} bytes) at {target_path}")
        return True
    except Exception as e:
        logger.error(f"[COOKIES] Failed to save cookie file: {e}")
        return False


def delete_cookie_file(user_id: int | None = None) -> bool:
    """Delete global cookie file."""
    try:
        target_path = GLOBAL_COOKIE_FILE
        deleted = False

        if os.path.exists(target_path):
            os.remove(target_path)
            deleted = True

        if os.path.exists(ROOT_COOKIE_FILE):
            try:
                os.remove(ROOT_COOKIE_FILE)
            except Exception:
                pass

        logger.info("[COOKIES] Deleted global cookie file")
        return deleted
    except Exception as e:
        logger.error(f"[COOKIES] Failed to delete cookie file: {e}")
        return False


def get_cookie_status(user_id: int | None = None) -> dict:
    """Return status dictionary about configured cookies."""
    path = get_effective_cookie_file()
    if not path or not os.path.exists(path):
        return {
            "has_cookie": False,
            "size_bytes": 0,
            "path": None,
        }

    size = os.path.getsize(path)
    return {
        "has_cookie": size > 0,
        "size_bytes": size,
        "path": path,
    }
