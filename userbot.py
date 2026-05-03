"""Userbot client — Pyrogram session for joining voice chats."""

import logging

from pyrogram import Client

from config import Config

log = logging.getLogger(__name__)


def create_userbot() -> Client:
    """Create and return a Pyrogram userbot client from SESSION_STRING."""
    return Client(
        name="music_userbot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        session_string=Config.SESSION_STRING,
    )
