"""YouTube search and stream extraction.

Strategy:
  - Search: yt-dlp native ytsearch1: (single pipeline, no third-party libs)
  - Short tracks (<15 min): download to /tmp for stability
  - Large media (≥15 min): direct HTTP stream URLs for instant playback
  - Anti-block stack: mweb+tv clients, cookies, PO tokens, EJS solver, IPv4
"""

import asyncio
import logging
import os
import shutil
import tempfile
import uuid

import yt_dlp

log = logging.getLogger(__name__)

# Directory for downloaded temp files
_TMP_DIR = tempfile.gettempdir()

# ── Cookies file path (Netscape format, exported from a real browser) ──
_COOKIES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cookies.txt")

# ── yt-dlp base opts with full anti-block stack ──
_BASE_YDL_OPTS: dict = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "geo_bypass": True,

    # ── Client order matters:
    # Putting mweb first as per LyriFusion architecture to support cookies
    "extractor_args": {
        "youtube": {
            "player_client": ["mweb", "tv"],
        },
        "youtubepot-bgutilhttp": {
            "base_url": ["http://127.0.0.1:4416"]
        }
    },
    
    # ── EJS Solver for JS Signatures ──
    "remote_components": ["ejs:github"],

    # ── IPv4 forcing: prevent IPv6 blackholes on cloud providers ──
    "source_address": "0.0.0.0",

    # ── Realistic User-Agent ──
    "headers": {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    },

    # ── Skip certificate issues on restrictive cloud networks ──
    "nocheckcertificate": True,

    # ── Retry resilience ──
    "fragment_retries": 10,
    "retries": 5,
    "extractor_retries": 3,
    "file_access_retries": 3,
    "socket_timeout": 30,
    "skip_unavailable_fragments": True,
}

# ── Conditionally add cookies and EJS solver ──
if os.path.isfile(_COOKIES_FILE):
    _BASE_YDL_OPTS["cookiefile"] = _COOKIES_FILE
    log.info("cookies.txt found — YouTube auth enabled")
else:
    log.warning("No cookies.txt found — YouTube may rate-limit more aggressively")

# EJS solver requires Node.js (installed in Docker image)
node_path = shutil.which("node")
if node_path:
    _BASE_YDL_OPTS["remote_components"] = ["ejs:github"]
    _BASE_YDL_OPTS["js_runtimes"] = {"node": {"path": node_path}}
    log.info(f"Node.js found at {node_path} — EJS signature solver enabled")


def _cleanup(path: str):
    """Silently delete a temp file."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


class YouTubeExtractor:
    """Search and extract via yt-dlp with full anti-block bypass stack."""

    @staticmethod
    def _is_url(text: str) -> bool:
        return text.startswith(("http://", "https://", "www."))

    @classmethod
    async def extract_info(
        cls, url_or_query: str, video: bool = False
    ) -> dict | None:
        """Download audio (or video) to /tmp and return local path + metadata.

        If YouTube fails entirely, falls back to SoundCloud search.
        """
        loop = asyncio.get_running_loop()

        # 1. Resolve query → URL
        original_query = url_or_query
        if not cls._is_url(url_or_query):
            # Bypass third-party search and use yt-dlp's native YouTube search
            url_or_query = f"ytsearch1:{url_or_query}"

        # 2. Try YouTube download
        result = await loop.run_in_executor(None, _download, url_or_query, video)

        return result


def _download(url: str, video: bool) -> dict | None:
    """Download or extract a track.
    
    If track is under 15 minutes, download to /tmp (highest stability).
    If track is 15 minutes or longer, return direct HTTP stream URLs (disk-safe, instant play).
    """
    uid = uuid.uuid4().hex
    out_template = os.path.join(_TMP_DIR, f"musicbot_{uid}.%(ext)s")

    if video:
        # Prioritize H264 (avc1) to drastically reduce ffmpeg decoding overhead
        # which eliminates video lag and stuttering on low-end servers.
        fmt = "bestvideo[height<=720][vcodec^=avc1]+bestaudio/bestvideo[height<=720]+bestaudio/best[height<=720]/best"
    else:
        fmt = "bestaudio*/best"

    ydl_opts_meta = {
        **_BASE_YDL_OPTS,
        "format": fmt,
    }

    try:
        # Step 1: Extract metadata first (no download)
        log.info("Extracting metadata for %r", url)
        with yt_dlp.YoutubeDL(ydl_opts_meta) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            return None

        # Resolve entry if search result
        video_info = info
        if "entries" in info:
            if not info["entries"]:
                log.error("No search results found for %r", url)
                return None
            video_info = info["entries"][0]

        duration = video_info.get("duration", 0)
        webpage_url = video_info.get("webpage_url", url)

        # Step 2: Extract direct HTTP stream URLs for instant playback (no downloading)
        log.info("Using direct HTTP streaming for %r (%ds)", webpage_url, duration)
        
        stream_url = None
        audio_url = None

        if video:
            req_formats = video_info.get("requested_formats")
            if req_formats and len(req_formats) >= 2:
                for f in req_formats:
                    if f.get("vcodec") != "none" and f.get("acodec") == "none":
                        stream_url = f["url"]
                    elif f.get("acodec") != "none" and f.get("vcodec") == "none":
                        audio_url = f["url"]
                if not stream_url or not audio_url:
                    stream_url = req_formats[0]["url"]
                    audio_url = req_formats[1]["url"]
            else:
                stream_url = video_info.get("url")
        else:
            req_formats = video_info.get("requested_formats")
            if req_formats:
                stream_url = req_formats[0]["url"]
            else:
                stream_url = video_info.get("url")

        if not stream_url:
            log.error("Failed to extract stream URL for %r", webpage_url)
            return None

        return {
            "title": video_info.get("title", "Unknown"),
            "duration": duration,
            "stream_url": stream_url,
            "audio_url": audio_url or "",
            "thumbnail": video_info.get("thumbnail", ""),
            "url": webpage_url,
            "uploader": video_info.get("uploader", "Unknown"),
            "local_file": False,
        }

    except Exception as e:
        log.error("Extraction failed for %r: %s", url, e)
        return None
