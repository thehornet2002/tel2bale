"""
Universal media downloader service supporting YouTube, Instagram, Spotify, and 1000+ sites.
Integrates yt-dlp, ffmpeg stream merging, audio extraction, and cookie management.
"""
import asyncio
import os
import re
import uuid
import aiohttp
import yt_dlp
from services.cookie_service import get_effective_cookie_file
from utils.logger import get_logger

logger = get_logger(__name__)

DOWNLOADS_DIR = "downloads"

YOUTUBE_REGEX = re.compile(r"(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/|embed/|v/|live/)|youtu\.be/)([\w\-]+)", re.IGNORECASE)
INSTAGRAM_REGEX = re.compile(r"(?:https?://)?(?:www\.)?(?:instagram\.com|instagr\.am)/(?:p|reel|tv|stories)/([\w\-_]+)", re.IGNORECASE)
SPOTIFY_REGEX = re.compile(r"(?:https?://)?(?:open\.spotify\.com|spotify\.link)/(?:track|album|playlist|intl-[a-z]{2}/track)/([\w\-]+)", re.IGNORECASE)
GENERIC_URL_REGEX = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)


def ensure_downloads_dir() -> None:
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)


def is_media_url(text: str) -> bool:
    """Check if text contains a recognized or downloadable media URL."""
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


async def fetch_spotify_metadata(url: str) -> dict | None:
    """Fetch Spotify track metadata using oEmbed without API credentials."""
    oembed_url = f"https://open.spotify.com/oembed?url={url}"
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
            async with session.get(oembed_url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    title = data.get("title", "")
                    thumbnail = data.get("thumbnail_url", "")
                    return {
                        "title": title,
                        "thumbnail": thumbnail,
                        "author": data.get("author_name", ""),
                    }
    except Exception as e:
        logger.warning(f"[DOWNLOADER] Spotify oEmbed error: {e}")
    return None


def _get_base_ydl_opts(user_id: int | None = None) -> dict:
    ensure_downloads_dir()
    opts = {
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "logtostderr": False,
        "geo_bypass": True,
        "socket_timeout": 30,
        "noplaylist": True,
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
    Returns:
        {
            "platform": str,
            "title": str,
            "duration": int | None,
            "thumbnail": str | None,
            "qualities": list[int],
            "url": str,
            "spotify_query": str | None
        }
    """
    platform = detect_platform(url)

    if platform == "spotify":
        meta = await fetch_spotify_metadata(url)
        title = meta.get("title") if meta else "Spotify Track"
        thumb = meta.get("thumbnail") if meta else None
        return {
            "platform": "spotify",
            "title": title,
            "duration": None,
            "thumbnail": thumb,
            "qualities": ["320k", "192k", "128k"],
            "url": url,
            "spotify_query": f"ytsearch1:{title} audio",
        }

    info = await asyncio.to_thread(_sync_extract_info, url, user_id)
    title = info.get("title") or "Media Download"
    duration = info.get("duration")
    thumbnail = info.get("thumbnail")

    formats = info.get("formats", [])
    heights = set()
    for f in formats:
        h = f.get("height")
        vcodec = f.get("vcodec")
        if h and vcodec != "none" and isinstance(h, int):
            heights.add(h)

    # Filter to standard user-friendly video heights
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
        "url": url,
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
    out_tmpl = os.path.join(DOWNLOADS_DIR, f"{unique_id}_%(title).50s.%(ext)s")

    opts = _get_base_ydl_opts(user_id)
    opts["outtmpl"] = out_tmpl

    target_url = spotify_query if (is_spotify and spotify_query) else url

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
        # Best available quality
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

        title = info_dict.get("title") or "downloaded_media"

    # Locate downloaded file in downloads directory matching unique_id prefix
    downloaded_file = None
    for fname in os.listdir(DOWNLOADS_DIR):
        if fname.startswith(unique_id):
            downloaded_file = os.path.join(DOWNLOADS_DIR, fname)
            break

    if not downloaded_file or not os.path.exists(downloaded_file):
        raise FileNotFoundError("فایل دانلودشده روی سرور یافت نشد.")

    file_size = os.path.getsize(downloaded_file)
    return downloaded_file, title, file_size


async def download_media(
    url: str,
    quality: str,
    user_id: int | None = None,
    is_spotify: bool = False,
    spotify_query: str | None = None,
) -> tuple[str, str, int]:
    """
    Download media asynchronously.
    Returns: (file_path, title, file_size_bytes)
    """
    unique_id = uuid.uuid4().hex[:12]
    return await asyncio.to_thread(
        _sync_download,
        url=url,
        quality=quality,
        user_id=user_id,
        out_id=unique_id,
        is_spotify=is_spotify,
        spotify_query=spotify_query,
    )
