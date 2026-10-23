"""
Cloudflare Turnstile Captcha and fallback challenge service.
Allows users to complete Cloudflare Turnstile verification or fallback challenge
before processing heavy media downloads (YouTube, Spotify, Instagram, etc.).
"""
import aiohttp
import config
from utils.logger import get_logger

logger = get_logger(__name__)

CF_SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def is_turnstile_configured() -> bool:
    """Return True if Cloudflare Turnstile keys and domain are configured."""
    return bool(config.CF_TURNSTILE_SITE_KEY and config.CF_TURNSTILE_SECRET_KEY and config.CF_TURNSTILE_DOMAIN)


def get_turnstile_domain() -> str:
    """Return the configured domain/URL for Turnstile verification page."""
    return config.CF_TURNSTILE_DOMAIN or ""


def build_turnstile_url(user_id: int, token: str) -> str:
    """Construct external Turnstile verification link with session token."""
    domain = get_turnstile_domain().rstrip("/")
    return f"{domain}/turnstile?user_id={user_id}&token={token}"


async def verify_turnstile_token(response_token: str, remote_ip: str | None = None) -> bool:
    """Verify Turnstile response token with Cloudflare API."""
    if not config.CF_TURNSTILE_SECRET_KEY:
        logger.warning("[TURNSTILE] Secret key not configured; skipping validation.")
        return False

    try:
        data = {
            "secret": config.CF_TURNSTILE_SECRET_KEY,
            "response": response_token,
        }
        if remote_ip:
            data["remoteip"] = remote_ip

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(CF_SITEVERIFY_URL, data=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    success = result.get("success", False)
                    if not success:
                        logger.warning(f"[TURNSTILE] Verification rejected: {result.get('error-codes')}")
                    return success
    except Exception as e:
        logger.error(f"[TURNSTILE] Error verifying token with Cloudflare: {e}")
    return False
