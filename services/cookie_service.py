"""
Cookie management service for yt-dlp and media downloaders.
Globally configured and managed exclusively by administrators (Netscape cookies.txt format).
Enforces 0600 file permissions and stores cookies exclusively inside protected cookies/ directory.
"""
import os
import stat
from utils.logger import get_logger

logger = get_logger(__name__)

COOKIES_DIR = "cookies"
GLOBAL_COOKIE_FILE = os.path.join(COOKIES_DIR, "global_cookies.txt")


def ensure_cookies_dir() -> None:
    """Ensure the cookies directory exists with restrictive directory permissions."""
    os.makedirs(COOKIES_DIR, exist_ok=True)
    try:
        os.chmod(COOKIES_DIR, stat.S_IRWXU)  # 0700
    except Exception:
        pass


def get_effective_cookie_file(user_id: int | None = None) -> str | None:
    """Resolve active global cookie file path inside protected cookies/ directory."""
    if os.path.exists(GLOBAL_COOKIE_FILE) and os.path.getsize(GLOBAL_COOKIE_FILE) > 0:
        return GLOBAL_COOKIE_FILE
    return None


def save_cookie_file(content: str | bytes, user_id: int | None = None) -> bool:
    """Save global cookie content with strict 0600 file permissions."""
    try:
        ensure_cookies_dir()
        target_path = GLOBAL_COOKIE_FILE

        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = content

        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        mode = stat.S_IRUSR | stat.S_IWUSR  # 0600
        fd = os.open(target_path, flags, mode)
        with open(fd, "wb") as f:
            f.write(content_bytes)

        # Remove any lingering legacy cookies.txt in root
        if os.path.exists("cookies.txt"):
            try:
                os.remove("cookies.txt")
            except Exception:
                pass

        logger.info(f"[COOKIES] Saved global cookie file ({len(content_bytes)} bytes) at {target_path} (mode 0600)")
        return True
    except Exception as e:
        logger.error(f"[COOKIES] Failed to save cookie file: {e}")
        return False


def delete_cookie_file(user_id: int | None = None) -> bool:
    """Delete global cookie file."""
    try:
        deleted = False
        if os.path.exists(GLOBAL_COOKIE_FILE):
            os.remove(GLOBAL_COOKIE_FILE)
            deleted = True

        if os.path.exists("cookies.txt"):
            try:
                os.remove("cookies.txt")
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
