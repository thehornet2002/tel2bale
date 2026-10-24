"""
Universal media downloader service supporting YouTube, Instagram, Spotify, and verified HTTPS media.
Integrates yt-dlp, ffmpeg stream merging, audio extraction, anti-SSRF protections,
concurrency limits, disk space checks, and safe filename sanitization.
"""
import asyncio
import os
import re
import shutil
import uuid
import aiohttp
import yt_dlp
from services.cookie_service import get_effective_cookie_file
from utils.parser import validate_public_https_url
from utils.logger import get_logger

logger = get_logger(__name__)

DOWNLOADS_DIR = "downloads"

# Concurrency limits: Max 3 concurrent downloads globally, 1 per user
_GLOBAL_DOWNLOAD_SEMAPHORE = asyncio.Semaphore(3)
_ACTIVE_USER_DOWNLOADS: set[int] = set()
_USER_LOCK = asyncio.Lock()

# Supported media platforms regexes
YOUTUBE_REGEX = re.compile(
    r"^(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/|embed/|v/|live/)|youtu\.be/)([\w\-]+)",
    re.IGNORECASE,
)
INSTAGRAM_REGEX = re.compile(
    r"^(?:https?://)?(?:www\.)?(?:instagram\.com|instagr\.am)/(?:p|reel|tv|stories)/([\w\-_]+)",
    re.IGNORECASE,
)
SPOTIFY_REGEX = re.compile(
    r"^(?:https?://)?(?:open\.spotify\.com|spotify\.link)/(?:track|album|playlist|intl-[a-z]{2}/track)/([\w\-]+)",
    re.IGNORECASE,
)
GENERIC_URL_REGEX = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)

# Allowed media file extensions
ALLOWED_MEDIA_EXTENSIONS = {
    ".mp4", ".mkv", ".webm", ".mov", ".avi",
    ".mp3", ".m4a", ".ogg", ".wav", ".aac", ".flac",
    ".jpg", ".jpeg", ".png", ".webp"
}


def ensure_downloads_dir() -> None:
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)


def check_disk_space(required_mb: int = 500) -> bool:
    """Check if server has at least required_mb free disk space."""
    try:
        ensure_downloads_dir()
        stat = shutil.disk_usage(DOWNLOADS_DIR)
        free_mb = stat.free / (1024 * 1024)
        return free_mb >= required_mb
    except Exception as e:
        logger.warning(f"[DOWNLOADER] Could not check disk space: {e}")
        return True


def is_media_url(text: str) -> bool:
    """Check if text matches recognized media platforms."""
    if not text:
        return False
    text = text.strip()
    return bool(
        YOUTUBE_REGEX.search(text)
        or INSTAGRAM_REGEX.search(text)
        or SPOTIFY_REGEX.search(text)
    )


def extract_media_url(text: str) -> str | None:
    """Extract first valid HTTP(S) URL from text."""
    if not text:
        return None
    m = GENERIC_URL_REGEX.search(text.strip())
    return m.group(0) if m else None


def detect_platform(url: str) -> str:
    """Identify media platform of URL."""
    if YOUTUBE_REGEX.search(url):
        return "youtube"
    if INSTAGRAM_REGEX.search(url):
        return "instagram"
    if SPOTIFY_REGEX.search(url):
        return "spotify"
    return "generic"


ALLOWED_MEDIA_DOMAINS = (
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "instagram.com",
    "www.instagram.com",
    "open.spotify.com",
    "spotify.link",
)


async def validate_media_target_url(url: str) -> str | None:
    """
    Validate target URL against SSRF and enforce exact domain allowlist:
    1. Ensures scheme is https://.
    2. Hostname strictly matches allowed domains without wildcards.
    3. Resolves DNS strictly against private/loopback/link-local/metadata IPs.
    """
    try:
        validated = await validate_public_https_url(url, resolve_dns=True)
        if not validated:
            return None

        from urllib.parse import urlparse
        parsed = urlparse(validated)
        host = (parsed.hostname or "").lower()

        if host not in ALLOWED_MEDIA_DOMAINS:
            logger.warning(f"[DOWNLOADER] Rejected URL domain not in media allowlist: {host}")
            return None

        return validated
    except Exception as e:
        logger.warning(f"[DOWNLOADER] URL validation failed for {url}: {e}")
        return None


async def fetch_spotify_metadata(url: str) -> dict | None:
    """Fetch Spotify track metadata using oEmbed with URL encoding and SSRF pre-validation."""
    from urllib.parse import quote
    validated_url = await validate_media_target_url(url)
    if not validated_url:
        return None

    encoded_url = quote(validated_url, safe="")
    oembed_url = f"https://open.spotify.com/oembed?url={encoded_url}"
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
            async with session.get(oembed_url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    title = data.get("title", "")
                    thumbnail = data.get("thumbnail_url", "")
                    clean_title = re.sub(r"[^\w\s\-.,()]", "", title)[:100]
                    return {
                        "title": clean_title,
                        "thumbnail": thumbnail,
                        "author": data.get("author_name", ""),
                    }
    except Exception as e:
        logger.warning(f"[DOWNLOADER] Spotify oEmbed error: {e}")
    return None


# Hard resource ceilings for media downloading
MAX_MEDIA_FILESIZE_BYTES = 500 * 1024 * 1024  # 500 MB hard ceiling
MAX_MEDIA_DURATION_SECONDS = 3600  # 1 hour max duration


def _get_base_ydl_opts(user_id: int | None = None) -> dict:
    ensure_downloads_dir()
    opts = {
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": False,  # TLS certificate verification strictly enabled
        "ignoreerrors": False,
        "logtostderr": False,
        "geo_bypass": True,
        "socket_timeout": 30,
        "noplaylist": True,
        "extract_flat": False,
        "max_filesize": MAX_MEDIA_FILESIZE_BYTES,
    }
    cookie_file = get_effective_cookie_file(user_id)
    if cookie_file:
        opts["cookiefile"] = cookie_file
        logger.debug(f"[DOWNLOADER] Using cookie file: {cookie_file}")
    return opts


def _sync_extract_info(url: str, user_id: int | None = None) -> dict:
    opts = _get_base_ydl_opts(user_id)
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


async def get_media_info(url: str, user_id: int | None = None) -> dict:
    """
    Extract media information and available resolutions.
    Validates target URL against SSRF before connecting.
    """
    platform = detect_platform(url)

    if platform == "spotify":
        meta = await fetch_spotify_metadata(url)
        title = meta.get("title") if meta else "Spotify Track"
        thumb = meta.get("thumbnail") if meta else None
        clean_search = re.sub(r"[^\w\s]", " ", title).strip()
        return {
            "platform": "spotify",
            "title": title,
            "duration": None,
            "thumbnail": thumb,
            "qualities": ["320k", "192k", "128k"],
            "url": url,
            "spotify_query": f"ytsearch1:{clean_search} audio",
        }

    # Strict SSRF check before querying yt-dlp
    validated_url = await validate_media_target_url(url)
    if not validated_url:
        raise ValueError("آدرس ارسالی نامعتبر یا غیرمجاز است (دسترسی به مقاصد محلی مسدود می‌باشد).")

    info = await asyncio.to_thread(_sync_extract_info, validated_url, user_id)
    raw_title = info.get("title") or "Media Download"
    title = re.sub(r"[^\w\s\-.,()]", "", raw_title)[:120]
    duration = info.get("duration")

    # Hard ceiling on duration (1 hour)
    if duration and duration > MAX_MEDIA_DURATION_SECONDS:
        raise ValueError(
            f"مدت زمان ویدیو ({duration // 60} دقیقه) از حداکثر سقف مجاز سرور ({MAX_MEDIA_DURATION_SECONDS // 60} دقیقه) بیشتر است."
        )

    thumbnail = info.get("thumbnail")

    formats = info.get("formats", [])
    heights = set()
    for f in formats:
        h = f.get("height")
        vcodec = f.get("vcodec")
        if h and vcodec != "none" and isinstance(h, int):
            heights.add(h)

    standard_heights = [1080, 720, 480, 360, 240]
    available_qualities = [h for h in standard_heights if any(h >= q for q in heights)]
    if not available_qualities and heights:
        available_qualities = sorted(list(heights), reverse=True)[:4]

    return {
        "platform": platform,
        "title": title,
        "duration": duration,
        "thumbnail": thumbnail,
        "qualities": available_qualities,
        "url": validated_url,
        "spotify_query": None,
    }


def _sync_download(
    url: str,
    quality: str,
    user_id: int | None = None,
    out_id: str | None = None,
    is_spotify: bool = False,
    spotify_query: str | None = None,
) -> tuple[str, str, int]:
    ensure_downloads_dir()
    unique_id = out_id or uuid.uuid4().hex[:12]
    # Pure server-generated safe filename pattern
    out_tmpl = os.path.join(DOWNLOADS_DIR, f"{unique_id}_media.%(ext)s")

    opts = _get_base_ydl_opts(user_id)
    opts["outtmpl"] = out_tmpl

    target_url = spotify_query if (is_spotify and spotify_query) else url

    if is_spotify and spotify_query:
        # Pre-check search result duration before downloading
        check_opts = _get_base_ydl_opts(user_id)
        with yt_dlp.YoutubeDL(check_opts) as ydl_check:
            search_res = ydl_check.extract_info(spotify_query, download=False)
            if "entries" in search_res and search_res["entries"]:
                first_entry = search_res["entries"][0]
                dur = first_entry.get("duration")
                if dur and dur > MAX_MEDIA_DURATION_SECONDS:
                    raise ValueError(
                        f"مدت زمان قطعه صوتی ({dur // 60} دقیقه) از حداکثر سقف مجاز سرور ({MAX_MEDIA_DURATION_SECONDS // 60} دقیقه) بیشتر است."
                    )

    if quality in ("audio", "320k", "192k", "128k") or is_spotify:
        bitrate = "320" if quality == "320k" else ("128" if quality == "128k" else "192")
        opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": bitrate,
            }],
        })
    elif quality.isdigit():
        height = int(quality)
        opts.update({
            "format": f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best",
            "merge_output_format": "mp4",
        })
    else:
        opts.update({
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
        })

    with yt_dlp.YoutubeDL(opts) as ydl:
        result = ydl.extract_info(target_url, download=True)
        if "entries" in result and result["entries"]:
            info_dict = result["entries"][0]
        else:
            info_dict = result

        raw_title = info_dict.get("title") or "downloaded_media"
        title = re.sub(r"[^\w\s\-.,()]", "", raw_title)[:120]

    # Locate downloaded file in downloads directory
    downloaded_file = None
    for fname in os.listdir(DOWNLOADS_DIR):
        if fname.startswith(unique_id):
            candidate = os.path.join(DOWNLOADS_DIR, fname)
            _, ext = os.path.splitext(candidate)
            if ext.lower() in ALLOWED_MEDIA_EXTENSIONS:
                downloaded_file = candidate
                break

    if not downloaded_file or not os.path.exists(downloaded_file):
        raise FileNotFoundError("فایل دانلودشده نامعتبر بوده یا یافت نشد.")

    file_size = os.path.getsize(downloaded_file)
    if file_size > MAX_MEDIA_FILESIZE_BYTES:
        try:
            os.remove(downloaded_file)
        except Exception:
            pass
        raise ValueError(f"حجم فایل نهایی ({file_size / (1024*1024):.1f} MB) از حداکثر سقف مجاز (500 MB) عبور کرد.")

    return downloaded_file, title, file_size


async def download_media(
    url: str,
    quality: str,
    user_id: int | None = None,
    is_spotify: bool = False,
    spotify_query: str | None = None,
) -> tuple[str, str, int]:
    """
    Download media asynchronously with concurrency control and disk space checks.
    """
    if not check_disk_space(required_mb=300):
        raise RuntimeError("فضای دیسک سرور برای دانلود رسانه جدید ناکافی است.")

    if not is_spotify:
        validated_url = await validate_media_target_url(url)
        if not validated_url:
            raise ValueError("آدرس مقصد معتبر نمی‌باشد یا به شبکه داخلی اشاره دارد.")
        url = validated_url

    # User concurrency guard: 1 active download per user
    if user_id:
        async with _USER_LOCK:
            if user_id in _ACTIVE_USER_DOWNLOADS:
                raise RuntimeError("شما هم‌اکنون یک دانلود فعال در حال انجام دارید. لطفاً منتظر اتمام آن بمانید.")
            _ACTIVE_USER_DOWNLOADS.add(user_id)

    unique_id = uuid.uuid4().hex[:12]
    try:
        async with _GLOBAL_DOWNLOAD_SEMAPHORE:
            return await asyncio.to_thread(
                _sync_download,
                url=url,
                quality=quality,
                user_id=user_id,
                out_id=unique_id,
                is_spotify=is_spotify,
                spotify_query=spotify_query,
            )
    finally:
        if user_id:
            async with _USER_LOCK:
                _ACTIVE_USER_DOWNLOADS.discard(user_id)
