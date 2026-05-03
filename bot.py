"""Bot command handlers — all 13 slash commands."""

import logging

from pyrogram import Client, filters
from pyrogram.types import Message

from config import Config
from player.queue import QueueManager
from player.stream import StreamManager
from utils.helpers import (
    build_now_playing,
    build_queue_message,
    build_queued_message,
    format_duration,
)
from utils.youtube import YouTubeExtractor

log = logging.getLogger(__name__)


def register_handlers(
    bot: Client,
    stream: StreamManager,
    queue: QueueManager,
) -> None:
    """Register all command handlers on the bot client."""

    # ── Helper to extract query from command ──
    def _get_query(message: Message) -> str | None:
        if len(message.command) < 2:
            return None
        return " ".join(message.command[1:])

    # ── /start ──────────────────────────────────────────────────
    @bot.on_message(filters.command("start") & filters.group)
    async def cmd_start(client: Client, message: Message):
        await message.reply_text(
            "👋 **Hey! I'm a Music Bot.**\n\n"
            "I can play audio and video in voice chats.\n"
            "Send `/help` for a list of commands.",
            quote=True,
        )

    @bot.on_message(filters.command("start") & filters.private)
    async def cmd_start_private(client: Client, message: Message):
        await message.reply_text(
            "👋 **Hey! I'm a Music Bot.**\n\n"
            "Add me to a group and start a voice chat,\n"
            "then use `/play <song name>` to play music!\n\n"
            "Send `/help` for all commands.",
        )

    # ── /help ───────────────────────────────────────────────────
    @bot.on_message(filters.command("help"))
    async def cmd_help(client: Client, message: Message):
        await message.reply_text(
            "**🎵 Music Bot Commands**\n\n"
            "▶️ `/play <url/query>` — Play audio\n"
            "🎥 `/vplay <url/query>` — Play video\n"
            "⏭ `/skip` — Skip current track\n"
            "⏹ `/stop` — Stop & leave VC\n"
            "⏸ `/pause` — Pause playback\n"
            "▶️ `/resume` — Resume playback\n"
            "📋 `/queue` — Show the queue\n"
            "🔊 `/volume <1-200>` — Set volume\n"
            "🔄 `/loop` — Toggle loop mode\n"
            "🔀 `/shuffle` — Shuffle queue\n"
            "🗑 `/clear` — Clear the queue",
            quote=True,
        )

    # ── /play & /vplay ──────────────────────────────────────────
    async def _handle_play(message: Message, video: bool = False):
        chat_id = message.chat.id
        query = _get_query(message)

        if not query:
            await message.reply_text(
                "❌ **Please provide a song name or URL.**\n"
                f"Example: `{'/' + ('vplay' if video else 'play')} alan walker faded`",
                quote=True,
            )
            return

        status_msg = await message.reply_text("🔍 **Searching…**", quote=True)

        # Extract stream info
        info = await YouTubeExtractor.extract_info(query, video=video)
        if not info:
            from pyrogram.errors import MessageNotModified
            try:
                await status_msg.edit_text("❌ **No results found.** Try a different query.")
            except MessageNotModified:
                pass
            return

        track = {
            "title": info["title"],
            "duration": info["duration"],
            "stream_url": info["stream_url"],
            "audio_url": info.get("audio_url", ""),
            "url": info["url"],
            "uploader": info["uploader"],
            "thumbnail": info["thumbnail"],
            "requested_by": message.from_user.id if message.from_user else 0,
            "video": video,
            "local_file": info.get("local_file", False),
        }

        # If nothing is playing, start immediately
        current = queue.get_current(chat_id)
        if current is None:
            queue.set_current(chat_id, track)
            try:
                await stream.play(
                    chat_id, 
                    track["stream_url"], 
                    audio_url=track.get("audio_url", ""),
                    video=video
                )
                await status_msg.edit_text(build_now_playing(track, video=video))
            except Exception as exc:
                queue.full_clear(chat_id)
                log.error("Play failed: %s", exc)
                await status_msg.edit_text(
                    "❌ **Failed to play.** Make sure a voice chat is active "
                    "and the userbot has permissions to join."
                )
        else:
            position = queue.add(chat_id, track)
            await status_msg.edit_text(build_queued_message(track, position))

    @bot.on_message(filters.command("play") & filters.group)
    async def cmd_play(client: Client, message: Message):
        await _handle_play(message, video=False)

    @bot.on_message(filters.command("vplay") & filters.group)
    async def cmd_vplay(client: Client, message: Message):
        await _handle_play(message, video=True)

    # ── /skip ───────────────────────────────────────────────────
    @bot.on_message(filters.command("skip") & filters.group)
    async def cmd_skip(client: Client, message: Message):
        chat_id = message.chat.id

        if not queue.get_current(chat_id):
            await message.reply_text("❌ **Nothing is playing.**", quote=True)
            return

        next_track = queue.skip(chat_id)
        if next_track:
            try:
                video = next_track.get("video", False)
                await stream.play(
                    chat_id, 
                    next_track["stream_url"], 
                    audio_url=next_track.get("audio_url", ""),
                    video=video
                )
                await message.reply_text(
                    f"⏭ **Skipped!**\n\n{build_now_playing(next_track, video=video)}",
                    quote=True,
                )
            except Exception as exc:
                log.error("Skip-play failed: %s", exc)
                await message.reply_text("❌ **Failed to play next track.**", quote=True)
        else:
            await stream.stop(chat_id)
            queue.full_clear(chat_id)
            await message.reply_text("⏭ **Skipped!** Queue is empty — left VC.", quote=True)

    # ── /stop ───────────────────────────────────────────────────
    @bot.on_message(filters.command("stop") & filters.group)
    async def cmd_stop(client: Client, message: Message):
        chat_id = message.chat.id
        await stream.stop(chat_id)
        queue.full_clear(chat_id)
        await message.reply_text("⏹ **Stopped playback and left voice chat.**", quote=True)

    # ── /pause ──────────────────────────────────────────────────
    @bot.on_message(filters.command("pause") & filters.group)
    async def cmd_pause(client: Client, message: Message):
        ok = await stream.pause(message.chat.id)
        if ok:
            await message.reply_text("⏸ **Paused.**", quote=True)
        else:
            await message.reply_text("❌ **Nothing to pause.**", quote=True)

    # ── /resume ─────────────────────────────────────────────────
    @bot.on_message(filters.command("resume") & filters.group)
    async def cmd_resume(client: Client, message: Message):
        ok = await stream.resume(message.chat.id)
        if ok:
            await message.reply_text("▶️ **Resumed.**", quote=True)
        else:
            await message.reply_text("❌ **Nothing to resume.**", quote=True)

    # ── /queue ──────────────────────────────────────────────────
    @bot.on_message(filters.command("queue") & filters.group)
    async def cmd_queue(client: Client, message: Message):
        chat_id = message.chat.id
        current = queue.get_current(chat_id)
        upcoming = queue.get_queue(chat_id)
        loop_mode = queue.get_loop_mode(chat_id)

        if not current and not upcoming:
            await message.reply_text("📋 **Queue is empty.**", quote=True)
            return

        text = build_queue_message(upcoming, current, loop_mode, Config.MAX_QUEUE_DISPLAY)
        await message.reply_text(text, quote=True)

    # ── /volume ─────────────────────────────────────────────────
    @bot.on_message(filters.command("volume") & filters.group)
    async def cmd_volume(client: Client, message: Message):
        arg = _get_query(message)
        if not arg or not arg.isdigit():
            await message.reply_text(
                "❌ **Usage:** `/volume <1-200>`\nExample: `/volume 150`",
                quote=True,
            )
            return

        vol = int(arg)
        if not (Config.MIN_VOLUME <= vol <= Config.MAX_VOLUME):
            await message.reply_text(
                f"❌ Volume must be between **{Config.MIN_VOLUME}** and **{Config.MAX_VOLUME}**.",
                quote=True,
            )
            return

        ok = await stream.set_volume(message.chat.id, vol)
        if ok:
            await message.reply_text(f"🔊 Volume set to **{vol}%**", quote=True)
        else:
            await message.reply_text("❌ **Failed to change volume.**", quote=True)

    # ── /loop ───────────────────────────────────────────────────
    @bot.on_message(filters.command("loop") & filters.group)
    async def cmd_loop(client: Client, message: Message):
        mode = queue.toggle_loop(message.chat.id)
        labels = {"off": "Off ➡️", "single": "🔂 Single Track", "all": "🔁 Entire Queue"}
        await message.reply_text(
            f"🔄 Loop mode: **{labels.get(mode.value, 'Off')}**", quote=True
        )

    # ── /shuffle ────────────────────────────────────────────────
    @bot.on_message(filters.command("shuffle") & filters.group)
    async def cmd_shuffle(client: Client, message: Message):
        chat_id = message.chat.id
        if queue.get_length(chat_id) < 2:
            await message.reply_text("❌ **Not enough tracks to shuffle.**", quote=True)
            return
        queue.shuffle(chat_id)
        await message.reply_text("🔀 **Queue shuffled!**", quote=True)

    # ── /clear ──────────────────────────────────────────────────
    @bot.on_message(filters.command("clear") & filters.group)
    async def cmd_clear(client: Client, message: Message):
        queue.clear(message.chat.id)
        await message.reply_text("🗑 **Queue cleared.** Current track still playing.", quote=True)
