"""Helper utilities — formatting, message builders."""


def format_duration(seconds: int | float | None) -> str:
    """Convert seconds to human-readable duration string.

    Examples: 245 → '4:05', 3661 → '1:01:01', None → 'Live'
    """
    if not seconds:
        return "Live"
    seconds = int(seconds)
    hrs, remainder = divmod(seconds, 3600)
    mins, secs = divmod(remainder, 60)
    if hrs:
        return f"{hrs}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def truncate(text: str, max_len: int = 40) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def build_now_playing(track: dict, video: bool = False) -> str:
    """Build a formatted 'Now Playing' message."""
    mode = "Video" if video else "Audio"
    title = track.get("title", "Unknown")
    duration = format_duration(track.get("duration"))
    uploader = track.get("uploader", "Unknown")
    url = track.get("url", "")

    lines = [
        f"🔊 **Now Playing on GlissStream**",
        "",
        f"• **Title:** [{truncate(title, 50)}]({url})" if url else f"• **Title:** {truncate(title, 50)}",
        f"• **Format:** {mode} (720p HD / 48kHz Stereo)",
        f"• **Duration:** `{duration}`",
        f"• **Source:** {uploader}",
    ]
    return "\n".join(lines)


def build_queued_message(track: dict, position: int) -> str:
    """Build a formatted 'Added to Queue' message."""
    title = track.get("title", "Unknown")
    duration = format_duration(track.get("duration"))
    return (
        f"📥 **Added to Queue**\n\n"
        f"• **Title:** {truncate(title, 50)}\n"
        f"• **Duration:** `{duration}`\n"
        f"• **Position:** Queue Slot #{position}"
    )


def build_queue_message(
    queue_list: list[dict],
    current: dict | None,
    loop_mode: str = "off",
    max_display: int = 15,
) -> str:
    """Build the full queue display message."""
    lines = ["📋 **GlissStream Queue Console**\n"]

    if current:
        title = truncate(current.get("title", "Unknown"), 45)
        dur = format_duration(current.get("duration"))
        lines.append(f"**Currently Streaming:**\n▶️ {title} — `{dur}`\n")

    lines.append("**Up Next:**")
    if not queue_list:
        lines.append("_No upcoming tracks._")
    else:
        for i, track in enumerate(queue_list[:max_display], 1):
            title = truncate(track.get("title", "Unknown"), 40)
            dur = format_duration(track.get("duration"))
            lines.append(f"`{i}.` {title} — `{dur}`")

        remaining = len(queue_list) - max_display
        if remaining > 0:
            lines.append(f"\n_... and {remaining} more_")

    loop_label = {"off": "Off", "single": "Single Track", "all": "Entire Queue"}
    lines.append("\n---")
    lines.append(f"🔄 **Loop Mode:** {loop_label.get(loop_mode, 'Off')} | 📊 **Active Pool:** {len(queue_list)} tracks")
    return "\n".join(lines)
