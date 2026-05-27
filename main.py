import os
import shutil
import subprocess
import asyncio
import logging

# ── Ensure FFmpeg/ffprobe are on PATH ──
def _setup_ffmpeg_path() -> None:
    """Add FFmpeg to PATH if not already available."""
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return  # Already on PATH

    # Common install locations (Windows)
    candidates = [
        os.path.expanduser(r"~\AppData\Local\ffmpegio\ffmpeg-downloader\ffmpeg\bin"),
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin",
        r"C:\ProgramData\chocolatey\bin",
    ]
    # Also check imageio-ffmpeg
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        candidates.insert(0, os.path.dirname(ffmpeg_exe))
    except ImportError:
        pass

    for path in candidates:
        ffmpeg_path = os.path.join(path, "ffmpeg.exe")
        ffprobe_path = os.path.join(path, "ffprobe.exe")
        if os.path.isfile(ffmpeg_path) and os.path.isfile(ffprobe_path):
            os.environ["PATH"] = path + os.pathsep + os.environ.get("PATH", "")
            return

_setup_ffmpeg_path()

# ── Monkey-patch: strip unsupported 'once' kwarg from logging calls ──
# yt-dlp calls logging.debug(msg, once=True) but the 'once' parameter
# was only introduced in Python 3.12. On 3.11 (our Docker base), this
# causes fatal crashes during downloads. Stripping it is harmless.
import sys
if sys.version_info < (3, 12):
    import logging as _logging
    _original_debug = _logging.Logger.debug
    _original_info = _logging.Logger.info
    _original_warning = _logging.Logger.warning

    def _patched_debug(self, msg, *args, **kwargs):
        kwargs.pop("once", None)
        return _original_debug(self, msg, *args, **kwargs)

    def _patched_info(self, msg, *args, **kwargs):
        kwargs.pop("once", None)
        return _original_info(self, msg, *args, **kwargs)

    def _patched_warning(self, msg, *args, **kwargs):
        kwargs.pop("once", None)
        return _original_warning(self, msg, *args, **kwargs)

    _logging.Logger.debug = _patched_debug
    _logging.Logger.info = _patched_info
    _logging.Logger.warning = _patched_warning
# ── End logging patch ──

# ── Monkey-patch: inject missing error class into pyrogram.errors ──
# py-tgcalls 2.2.11 imports GroupcallForbidden which pyrogram 2.0.106 lacks.
import pyrogram.errors as _pe

if not hasattr(_pe, "GroupcallForbidden"):

    class GroupcallForbidden(Exception):
        """Stub: The group call has forbidden the action."""
        ID = "GROUPCALL_FORBIDDEN"
        MESSAGE = "The group call has forbidden the action."

    _pe.GroupcallForbidden = GroupcallForbidden
    # Also inject into the exceptions sub-module if it exists
    if hasattr(_pe, "exceptions"):
        _pe.exceptions.GroupcallForbidden = GroupcallForbidden
# ── End patch ──



from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types import Update

from bot import register_handlers
from config import Config
from player.queue import QueueManager
from player.stream import StreamManager
from userbot import create_userbot
from utils.youtube import YouTubeExtractor

# ── Logging ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("main")


def _cleanup_stray_temp_files() -> None:
    """Scan the temp directory and delete any files starting with 'musicbot_' from past runs."""
    import tempfile
    tmp_dir = tempfile.gettempdir()
    log.info(f"Cleaning up stray temp files in {tmp_dir}...")
    count = 0
    try:
        for fname in os.listdir(tmp_dir):
            if fname.startswith("musicbot_"):
                fpath = os.path.join(tmp_dir, fname)
                try:
                    os.remove(fpath)
                    count += 1
                except Exception:
                    pass
        if count > 0:
            log.info(f"Successfully cleaned up {count} stray temp files")
    except Exception as e:
        log.warning(f"Error during stray temp files cleanup: {e}")


def _setup_pot_server() -> None:
    """Clones, builds, and starts the PO Token provider background service."""
    repo_url = "https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git"
    repo_dir = "bgutil-ytdlp-pot-provider"
    server_dir = os.path.join(repo_dir, "server")

    if not os.path.exists(repo_dir):
        log.info("PO Token provider not found. Cloning...")
        try:
            subprocess.run(["git", "clone", "--single-branch", "--branch", "1.3.1", repo_url, repo_dir], check=True)
            log.info("Installing dependencies for PO Token provider...")
            subprocess.run(["npm", "ci", "--include=dev"], cwd=server_dir, check=True)
            log.info("Installing typescript compiler...")
            subprocess.run(["npm", "install", "typescript"], cwd=server_dir, check=True)
            log.info("Building PO Token provider...")
            subprocess.run(["npx", "--yes", "tsc"], cwd=server_dir, check=True)
        except Exception as e:
            log.error(f"Failed to setup PO Token provider: {e}")
            return

    # Check if port 4416 is already in use (e.g. LyrifusionBot's PO Token server)
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(1)
        sock.connect(("127.0.0.1", 4416))
        sock.close()
        log.info("PO Token provider already running on port 4416 — skipping spawn")
        return
    except (ConnectionRefusedError, OSError):
        sock.close()

    log.info("Starting PO Token provider on port 4416...")
    try:
        with open(os.path.join(server_dir, "pot_server_musicbot.log"), "w") as pot_log:
            subprocess.Popen(
                ["node", "--experimental-require-module", "build/main.js"],
                cwd=server_dir,
                stdout=pot_log,
                stderr=pot_log,
            )
    except Exception as e:
        log.error(f"Failed to start PO Token provider: {e}")


async def main() -> None:
    # ── Clean up stray files from past crashes ──
    _cleanup_stray_temp_files()

    # ── Setup background services ──
    _setup_pot_server()

    # ── Validate config ──
    Config.validate()
    log.info("Config validated ✓")

    # ── Create clients ──
    userbot = create_userbot()
    bot = Client(
        name="music_bot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
    )

    # ── PyTgCalls wraps the userbot ──
    pytgcalls = PyTgCalls(userbot)

    # ── Managers ──
    queue_mgr = QueueManager()
    stream_mgr = StreamManager(pytgcalls)

    # ── Auto-advance callback ──
    async def on_track_end(chat_id: int) -> None:
        """Called when a stream finishes — play next track or leave VC."""
        from player.queue import LoopMode
        from utils.youtube import _cleanup

        # Grab the track that just finished BEFORE advancing
        prev_track = queue_mgr.get_current(chat_id)
        loop_mode = queue_mgr.get_loop_mode(chat_id)

        next_track = queue_mgr.advance(chat_id)

        # Clean up the old track's local file ONLY if it is not being reused.
        # In SINGLE loop mode, advance() returns the same track — don't delete.
        # In ALL loop mode, advance() re-appends it to the queue — don't delete.
        if prev_track and prev_track.get("local_file"):
            if loop_mode not in (LoopMode.SINGLE.value, LoopMode.ALL.value):
                _cleanup(prev_track.get("stream_url", ""))

        if next_track:
            try:
                video = next_track.get("video", False)
                await stream_mgr.play(
                    chat_id, 
                    next_track["stream_url"], 
                    audio_url=next_track.get("audio_url", ""),
                    video=video
                )
                log.info("Auto-advanced to: %s", next_track.get("title", "?"))
            except Exception as exc:
                log.error("Auto-advance failed in chat %d: %s", chat_id, exc)
                queue_mgr.full_clear(chat_id)
        else:
            await stream_mgr.stop(chat_id)
            queue_mgr.full_clear(chat_id)
            log.info("Queue empty in chat %d — left VC", chat_id)

    stream_mgr.set_on_track_end(on_track_end)

    # ── Register PyTgCalls stream-end handler ──
    @pytgcalls.on_update()
    async def on_update(client: PyTgCalls, update: Update) -> None:
        """Handle all PyTgCalls updates — detect stream end."""
        # The update object has chat_id and status attributes
        if hasattr(update, "chat_id") and hasattr(update, "status"):
            from pytgcalls.types import MediaStream

            # Check if the stream has ended
            status_name = str(update.status).lower() if update.status else ""
            if "ended" in status_name or "stopped" in status_name:
                await stream_mgr.handle_stream_end(update.chat_id)

    # ── Register bot command handlers ──
    register_handlers(bot, stream_mgr, queue_mgr)
    log.info("Command handlers registered ✓")

    # ── Start everything ──
    await userbot.start()
    log.info("Userbot started ✓")

    await bot.start()
    log.info("Bot started ✓")

    await pytgcalls.start()
    log.info("PyTgCalls started ✓")

    log.info("━" * 50)
    log.info("🎵 Music Bot is running! Press Ctrl+C to stop.")
    log.info("━" * 50)

    # ── Start dummy web server for Cloud Providers (e.g. Hugging Face) ──
    from aiohttp import web
    async def handle_ping(request):
        return web.Response(text="Bot is alive and streaming! 🎵")
    
    web_app = web.Application()
    web_app.router.add_get("/", handle_ping)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 7860)
    await site.start()
    log.info("Dummy web server started on port 7860 ✓")

    # ── Keep alive ──
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        log.info("Shutting down…")
    finally:
        await pytgcalls.stop() if hasattr(pytgcalls, "stop") else None
        await bot.stop()
        await userbot.stop()
        log.info("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
