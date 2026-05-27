"""PyTgCalls stream manager — play, pause, resume, volume, on_stream_end."""

import logging
from typing import Callable, Optional

from pytgcalls import PyTgCalls
from pytgcalls.types import AudioQuality, MediaStream, VideoQuality

log = logging.getLogger(__name__)


class StreamManager:
    """Wraps PyTgCalls to manage voice-chat streaming per chat."""

    def __init__(self, pytgcalls: PyTgCalls) -> None:
        self._call = pytgcalls
        self._active: dict[int, dict] = {}   # chat_id → {video: bool}
        self._on_track_end: Optional[Callable] = None

    # ── Public API ──────────────────────────────────────────────

    async def play(
        self,
        chat_id: int,
        stream_url: str,
        audio_url: str = "",
        video: bool = False,
    ) -> None:
        """Join VC and start streaming audio (or audio+video)."""
        if video:
            media = MediaStream(
                stream_url,
                audio_path=audio_url if audio_url else None,
                audio_parameters=AudioQuality.STUDIO,
                video_parameters=VideoQuality.HD_720p,
                ffmpeg_parameters="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            )
        else:
            media = MediaStream(
                stream_url,
                audio_parameters=AudioQuality.STUDIO,
                video_flags=MediaStream.Flags.IGNORE,
                ffmpeg_parameters="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            )

        try:
            await self._call.play(chat_id, media)
            self._active[chat_id] = {"video": video}
            log.info("Started %s stream in chat %d", "video" if video else "audio", chat_id)
        except Exception as exc:
            log.error("Failed to play in chat %d: %s", chat_id, exc)
            raise

    async def pause(self, chat_id: int) -> bool:
        """Pause the current stream. Returns True on success."""
        try:
            await self._call.pause(chat_id)
            return True
        except Exception as exc:
            log.error("Failed to pause in chat %d: %s", chat_id, exc)
            return False

    async def resume(self, chat_id: int) -> bool:
        """Resume the current stream. Returns True on success."""
        try:
            await self._call.resume(chat_id)
            return True
        except Exception as exc:
            log.error("Failed to resume in chat %d: %s", chat_id, exc)
            return False

    async def stop(self, chat_id: int) -> bool:
        """Stop streaming and leave the voice chat."""
        try:
            await self._call.leave_call(chat_id)
            self._active.pop(chat_id, None)
            log.info("Left VC in chat %d", chat_id)
            return True
        except Exception as exc:
            log.error("Failed to stop in chat %d: %s", chat_id, exc)
            return False

    async def set_volume(self, chat_id: int, volume: int) -> bool:
        """Set volume (1–200). Returns True on success."""
        volume = max(1, min(200, volume))
        try:
            await self._call.change_volume_call(chat_id, volume)
            return True
        except Exception as exc:
            log.error("Failed to set volume in chat %d: %s", chat_id, exc)
            return False

    def is_active(self, chat_id: int) -> bool:
        return chat_id in self._active

    def is_video(self, chat_id: int) -> bool:
        info = self._active.get(chat_id, {})
        return info.get("video", False)

    def set_on_track_end(self, callback: Callable) -> None:
        """Register the auto-advance callback."""
        self._on_track_end = callback

    async def handle_stream_end(self, chat_id: int) -> None:
        """Called when a stream ends — triggers auto-advance."""
        self._active.pop(chat_id, None)
        if self._on_track_end:
            await self._on_track_end(chat_id)
