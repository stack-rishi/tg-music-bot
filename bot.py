"""Bot command handlers — all 13 slash commands."""

import logging

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import Config
from player.queue import QueueManager
from player.stream import StreamManager
from utils.helpers import (
    build_now_playing,
    build_queue_message,
    build_queued_message,
    format_duration,
    get_now_playing_markup,
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
        caption = (
            f"Hey {message.from_user.first_name if message.from_user else 'there'},\n"
            f"This is **GlissStream** !\n\n"
            f"A music player bot with some awesome and useful features.\n\n"
            f"_Click on the help button for more info._"
        )
        
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Help", callback_data="cb_help")],
            [InlineKeyboardButton("Support", url="https://t.me/Ri5h11"), InlineKeyboardButton("Source", url="https://github.com/")],
        ])
        
        await message.reply_photo(
            photo="catfortg.jpeg",
            caption=caption,
            reply_markup=reply_markup
        )

    HELP_TEXT = (
        "⚡ **GlissStream Command Console**\n\n"
        "• `/play <query/url>` — Stream high-fidelity audio\n"
        "• `/vplay <query/url>` — Stream HD video (up to 720p)\n"
        "• `/skip` — Advance to the next track in the queue\n"
        "• `/stop` — Terminate the current stream and disconnect\n"
        "• `/pause` — Suspend playback temporarily\n"
        "• `/resume` — Continue playback of the suspended stream\n"
        "• `/queue` — View all upcoming tracks and current mode\n"
        "• `/volume <1-200>` — Calibrate stream volume\n"
        "• `/loop` — Cycle loop settings (Single / Queue / Off)\n"
        "• `/shuffle` — Randomize upcoming tracks\n"
        "• `/clear` — Wipe the upcoming queue\n\n"
        "🔧 **Support & Operations:**\n"
        "For technical issues or assistance, contact the systems owner: @Ri5h11."
    )

    @bot.on_message(filters.command("start") & filters.private)
    async def cmd_start_private(client: Client, message: Message):
        bot_me = await client.get_me()
        bot_username = bot_me.username
        
        caption = (
            f"Hey {message.from_user.first_name if message.from_user else 'there'},\n"
            f"This is **GlissStream** !\n\n"
            f"A music player bot with some awesome and useful features.\n\n"
            f"_Click on the help button for more info._"
        )
        
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Add me to your group", url=f"https://t.me/{bot_username}?startgroup=true")],
            [InlineKeyboardButton("Help", callback_data="cb_help")],
            [InlineKeyboardButton("Support", url="https://t.me/Ri5h11"), InlineKeyboardButton("Source", url="https://github.com/")],
        ])
        
        await message.reply_photo(
            photo="catfortg.jpeg",
            caption=caption,
            reply_markup=reply_markup
        )

    # ── /help ───────────────────────────────────────────────────
    @bot.on_message(filters.command("help"))
    async def cmd_help(client: Client, message: Message):
        await message.reply_text(HELP_TEXT, quote=True)

    # ── /play & /vplay ──────────────────────────────────────────
    async def _handle_play(message: Message, video: bool = False):
        chat_id = message.chat.id
        query = _get_query(message)

        if not query:
            await message.reply_text(
                "Please provide a song name or URL.\n"
                f"Example: `{'/' + ('vplay' if video else 'play')} alan walker faded`",
                quote=True,
            )
            return

        status_msg = await message.reply_text("Searching...", quote=True)

        # Extract stream info
        info = await YouTubeExtractor.extract_info(query, video=video)
        if not info:
            from pyrogram.errors import MessageNotModified
            try:
                await status_msg.edit_text("No results found. Please try a different query.")
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
                await status_msg.edit_text(
                    build_now_playing(track, video=video),
                    reply_markup=get_now_playing_markup(is_paused=False),
                )
            except Exception as exc:
                queue.full_clear(chat_id)
                log.error("Play failed: %s", exc)
                await status_msg.edit_text(
                    "Playback failed. Make sure a voice chat is active "
                    "and the userbot has permission to join."
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
            await message.reply_text("There is currently nothing playing.", quote=True)
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
                    build_now_playing(next_track, video=video),
                    reply_markup=get_now_playing_markup(is_paused=False),
                    quote=True,
                )
            except Exception as exc:
                log.error("Skip-play failed: %s", exc)
                await message.reply_text("Failed to play the next track.", quote=True)
        else:
            await stream.stop(chat_id)
            queue.full_clear(chat_id)
            await message.reply_text("Skipped. The queue is now empty. Left the voice chat.", quote=True)

    # ── /stop ───────────────────────────────────────────────────
    @bot.on_message(filters.command("stop") & filters.group)
    async def cmd_stop(client: Client, message: Message):
        chat_id = message.chat.id
        await stream.stop(chat_id)
        queue.full_clear(chat_id)
        await message.reply_text("Stopped playback and left the voice chat.", quote=True)

    # ── /pause ──────────────────────────────────────────────────
    @bot.on_message(filters.command("pause") & filters.group)
    async def cmd_pause(client: Client, message: Message):
        ok = await stream.pause(message.chat.id)
        if ok:
            await message.reply_text("Playback paused.", quote=True)
        else:
            await message.reply_text("There is nothing playing to pause.", quote=True)

    # ── /resume ─────────────────────────────────────────────────
    @bot.on_message(filters.command("resume") & filters.group)
    async def cmd_resume(client: Client, message: Message):
        ok = await stream.resume(message.chat.id)
        if ok:
            await message.reply_text("Playback resumed.", quote=True)
        else:
            await message.reply_text("There is nothing to resume.", quote=True)

    # ── /queue ──────────────────────────────────────────────────
    @bot.on_message(filters.command("queue") & filters.group)
    async def cmd_queue(client: Client, message: Message):
        chat_id = message.chat.id
        current = queue.get_current(chat_id)
        upcoming = queue.get_queue(chat_id)
        loop_mode = queue.get_loop_mode(chat_id)

        if not current and not upcoming:
            await message.reply_text("The queue is currently empty.", quote=True)
            return

        text = build_queue_message(upcoming, current, loop_mode, Config.MAX_QUEUE_DISPLAY)
        await message.reply_text(text, quote=True)

    # ── /volume ─────────────────────────────────────────────────
    @bot.on_message(filters.command("volume") & filters.group)
    async def cmd_volume(client: Client, message: Message):
        arg = _get_query(message)
        if not arg or not arg.isdigit():
            await message.reply_text(
                "Usage: `/volume <1-200>`\nExample: `/volume 150`",
                quote=True,
            )
            return

        vol = int(arg)
        if not (Config.MIN_VOLUME <= vol <= Config.MAX_VOLUME):
            await message.reply_text(
                f"Volume must be between {Config.MIN_VOLUME} and {Config.MAX_VOLUME}.",
                quote=True,
            )
            return

        ok = await stream.set_volume(message.chat.id, vol)
        if ok:
            await message.reply_text(f"Volume set to {vol}%.", quote=True)
        else:
            await message.reply_text("Failed to change the volume.", quote=True)

    # ── /loop ───────────────────────────────────────────────────
    @bot.on_message(filters.command("loop") & filters.group)
    async def cmd_loop(client: Client, message: Message):
        mode = queue.toggle_loop(message.chat.id)
        labels = {"off": "Off", "single": "Single Track", "all": "Entire Queue"}
        await message.reply_text(
            f"Loop mode set to: **{labels.get(mode.value, 'Off')}**", quote=True
        )

    # ── /shuffle ────────────────────────────────────────────────
    @bot.on_message(filters.command("shuffle") & filters.group)
    async def cmd_shuffle(client: Client, message: Message):
        chat_id = message.chat.id
        if queue.get_length(chat_id) < 2:
            await message.reply_text("There are not enough tracks in the queue to shuffle.", quote=True)
            return
        queue.shuffle(chat_id)
        await message.reply_text("Queue shuffled.", quote=True)

    # ── /clear ──────────────────────────────────────────────────
    @bot.on_message(filters.command("clear") & filters.group)
    async def cmd_clear(client: Client, message: Message):
        queue.clear(message.chat.id)
        await message.reply_text("Upcoming queue cleared. The current track will continue playing.", quote=True)

    # ── Inline Callbacks ────────────────────────────────────────
    @bot.on_callback_query(filters.regex(r"^cb_"))
    async def handle_callbacks(client: Client, callback_query):
        data = callback_query.data

        if data == "cb_help":
            await callback_query.edit_message_caption(
                caption=HELP_TEXT,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Back", callback_data="cb_start")]
                ])
            )
            await callback_query.answer()
            return
            
        elif data == "cb_start":
            is_private = callback_query.message.chat.type == "private"
            bot_me = await client.get_me()
            bot_username = bot_me.username
            caption = (
                f"Hey {callback_query.from_user.first_name if callback_query.from_user else 'there'},\n"
                f"This is **GlissStream** !\n\n"
                f"A music player bot with some awesome and useful features.\n\n"
                f"_Click on the help button for more info._"
            )
            if is_private:
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Add me to your group", url=f"https://t.me/{bot_username}?startgroup=true")],
                    [InlineKeyboardButton("Help", callback_data="cb_help")],
                    [InlineKeyboardButton("Support", url="https://t.me/Ri5h11"), InlineKeyboardButton("Source", url="https://github.com/")],
                ])
            else:
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Help", callback_data="cb_help")],
                    [InlineKeyboardButton("Support", url="https://t.me/Ri5h11"), InlineKeyboardButton("Source", url="https://github.com/")],
                ])
            await callback_query.edit_message_caption(
                caption=caption,
                reply_markup=reply_markup
            )
            await callback_query.answer()
            return

        chat_id = callback_query.message.chat.id

        if data == "cb_pause":
            ok = await stream.pause(chat_id)
            if ok:
                try:
                    await callback_query.edit_message_reply_markup(
                        reply_markup=get_now_playing_markup(is_paused=True)
                    )
                    await callback_query.answer("Playback paused.")
                except Exception:
                    pass
            else:
                await callback_query.answer("Failed to pause playback.", show_alert=True)

        elif data == "cb_resume":
            ok = await stream.resume(chat_id)
            if ok:
                try:
                    await callback_query.edit_message_reply_markup(
                        reply_markup=get_now_playing_markup(is_paused=False)
                    )
                    await callback_query.answer("Playback resumed.")
                except Exception:
                    pass
            else:
                await callback_query.answer("Failed to resume playback.", show_alert=True)

        elif data == "cb_skip":
            if not queue.get_current(chat_id):
                await callback_query.answer("There is currently nothing playing.", show_alert=True)
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
                    await callback_query.message.edit_text(
                        build_now_playing(next_track, video=video),
                        reply_markup=get_now_playing_markup(is_paused=False)
                    )
                    await callback_query.answer("Skipped to next track.")
                except Exception as exc:
                    log.error("Callback skip failed: %s", exc)
                    await callback_query.answer("Failed to stream the next track.", show_alert=True)
            else:
                await stream.stop(chat_id)
                queue.full_clear(chat_id)
                try:
                    await callback_query.message.edit_text(
                        "Skipped. The queue is now empty. Disconnected from voice chat.",
                        reply_markup=None
                    )
                except Exception:
                    pass
                await callback_query.answer("Queue empty. Disconnected.")

        elif data == "cb_stop":
            await stream.stop(chat_id)
            queue.full_clear(chat_id)
            try:
                await callback_query.message.edit_text(
                    "Stopped playback and left the voice chat.",
                    reply_markup=None
                )
            except Exception:
                pass
            await callback_query.answer("Playback stopped.")

        elif data == "cb_loop":
            mode = queue.toggle_loop(chat_id)
            labels = {"off": "Off", "single": "Single Track", "all": "Entire Queue"}
            await callback_query.answer(f"Loop setting: {labels.get(mode.value, 'Off')}")

        elif data == "cb_queue":
            current = queue.get_current(chat_id)
            upcoming = queue.get_queue(chat_id)
            loop_mode = queue.get_loop_mode(chat_id)

            if not current and not upcoming:
                await callback_query.answer("The queue is currently empty.", show_alert=True)
                return

            text = build_queue_message(upcoming, current, loop_mode, 10)
            await callback_query.message.reply_text(text, quote=False)
            await callback_query.answer()

        elif data == "cb_shuffle":
            if queue.get_length(chat_id) < 2:
                await callback_query.answer("Not enough tracks in the queue to shuffle.", show_alert=True)
                return
            queue.shuffle(chat_id)
            await callback_query.answer("Queue shuffled.")
