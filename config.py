"""Configuration module — loads and validates environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration loaded from environment variables."""

    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    SESSION_STRING = os.getenv("SESSION_STRING", "")
    SUDO_USERS = [
        int(uid.strip())
        for uid in os.getenv("SUDO_USERS", "").split(",")
        if uid.strip().isdigit()
    ]

    # ── Playback defaults ──
    DEFAULT_VOLUME = 100
    MAX_VOLUME = 200
    MIN_VOLUME = 1
    MAX_QUEUE_DISPLAY = 15  # Max tracks shown in /queue

    @classmethod
    def validate(cls) -> None:
        """Raise RuntimeError if required env vars are missing."""
        missing = []
        if cls.API_ID == 0:
            missing.append("API_ID")
        if not cls.API_HASH:
            missing.append("API_HASH")
        if not cls.BOT_TOKEN:
            missing.append("BOT_TOKEN")
        if not cls.SESSION_STRING:
            missing.append("SESSION_STRING")
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                "Copy .env.example to .env and fill in the values."
            )
