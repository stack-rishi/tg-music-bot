"""YouTube search and stream extraction.

Strategy:
  - Search: ytmusicapi (native API, immune to bot detection)
  - Extraction: yt-dlp download to /tmp with full anti-block stack:
      • Client spoofing (mweb + tv) to bypass SABR streaming
      • cookies.txt authentication to look like a real user
      • IPv4 forcing to avoid IPv6 blackholes on cloud providers
      • EJS solver for JavaScript signature challenges
      • SoundCloud fallback if YouTube completely fails
"""

import asyncio
import logging
import os
import shutil
import tempfile
import uuid

import yt_dlp
from ytmusicapi import YTMusic

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

    # ── Client spoofing: bypass SABR streaming blocks ──
    # mweb bypasses SABR *and* supports cookies (unlike ios client)
    # tv is a secondary fallback client
    "extractor_args": {
        "youtube": {
            "player_client": ["mweb", "tv"],
        },
    },

    # ── IPv4 forcing: prevent IPv6 blackholes on cloud providers ──
    "source_address": "0.0.0.0",

    # ── Realistic User-Agent matching mweb client ──
    "headers": {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Mobile Safari/537.36"
        ),
    },

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
if shutil.which("node"):
    _BASE_YDL_OPTS["remote_components"] = ["ejs:github"]
    log.info("Node.js found — EJS signature solver enabled")


def _cleanup(path: str):
    """Silently delete a temp file."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


class YouTubeExtractor:
    """Search via ytmusicapi, download via yt-dlp with full bypass stack."""

    @staticmethod
    def _is_url(text: str) -> bool:
        return text.startswith(("http://", "https://", "www."))

    @classmethod
    async def search(cls, query: str, max_results: int = 5) -> list[dict]:
        """Search YouTube Music (no scraping, no bot detection)."""
        loop = asyncio.get_running_loop()

        def _do_search():
            try:
                ytm = YTMusic()
                results = ytm.search(query, filter="songs", limit=max_results)
                return results or []
            except Exception as e:
                log.error("YTMusic search error: %s", e)
                return []

        raw = await loop.run_in_executor(None, _do_search)

        formatted = []
        for r in raw:
            video_id = r.get("videoId")
            if not video_id:
                continue
            artists = r.get("artists", [])
            formatted.append({
                "title": r.get("title", "Unknown"),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "duration": r.get("duration_seconds", 0),
                "uploader": artists[0]["name"] if artists else "Unknown",
            })
        return formatted

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
            results = await cls.search(url_or_query, max_results=1)
            if not results:
                # If ytmusicapi search also fails, try direct yt-dlp search
                url_or_query = f"ytsearch1:{url_or_query}"
            else:
                url_or_query = results[0]["url"]

        # 2. Try YouTube download
        result = await loop.run_in_executor(None, _download, url_or_query, video)

        # 3. SoundCloud fallback if YouTube failed
        if result is None and not cls._is_url(original_query):
            log.warning("YouTube failed for %r — trying SoundCloud fallback", original_query)
            sc_query = f"scsearch1:{original_query}"
            result = await loop.run_in_executor(None, _download, sc_query, video)
            if result:
                log.info("SoundCloud fallback succeeded for %r", original_query)

        return result


def _download(url: str, video: bool) -> dict | None:
    """Download a track to /tmp. Returns metadata dict or None."""
    uid = uuid.uuid4().hex
    out_template = os.path.join(_TMP_DIR, f"musicbot_{uid}.%(ext)s")

    if video:
        fmt = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
    else:
        fmt = "bestaudio/best"

    ydl_opts = {
        **_BASE_YDL_OPTS,
        "format": fmt,
        "outtmpl": out_template,
        # Merge video+audio if needed (requires ffmpeg)
        "postprocessors": [] if video else [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        if not info:
            return None

        # yt-dlp renames the file after post-processing;
        # find it by scanning for the uid prefix
        downloaded = None
        for fname in os.listdir(_TMP_DIR):
            if fname.startswith(f"musicbot_{uid}"):
                downloaded = os.path.join(_TMP_DIR, fname)
                break

        if not downloaded or not os.path.exists(downloaded):
            log.error("Downloaded file not found for %r", url)
            return None

        return {
            "title": info.get("title", "Unknown"),
            "duration": info.get("duration", 0),
            "stream_url": downloaded,   # Local file path!
            "audio_url": "",            # Not needed for local files
            "thumbnail": info.get("thumbnail", ""),
            "url": info.get("webpage_url", url),
            "uploader": info.get("uploader", "Unknown"),
            "local_file": True,         # Flag so bot can clean up later
        }
    except Exception as e:
        log.error("yt-dlp download failed for %r: %s", url, e)
        return None
