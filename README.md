---
title: Telegram Music Bot
emoji: 🎵
colorFrom: purple
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# 🎵 Telegram VC Music Bot

A production-ready Telegram voice chat music & video player bot built with **Pyrogram** + **py-tgcalls** + **yt-dlp**.

## Features

- 🔊 Play audio from YouTube (URL or search query)
- 🎥 Stream video in voice chats
- 📋 Per-chat queue with auto-advance
- 🔄 Loop modes (off / single / all)
- 🔀 Queue shuffle
- 🔊 Volume control (1–200)
- 🗑 Clear queue
- ⏸ Pause / Resume
- ⏭ Skip tracks

## Commands

| Command | Description |
|---|---|
| `/play <url/query>` | Play audio in VC |
| `/vplay <url/query>` | Play video in VC |
| `/skip` | Skip to next track |
| `/stop` | Stop & leave VC |
| `/pause` | Pause playback |
| `/resume` | Resume playback |
| `/queue` | Show the queue |
| `/volume <1-200>` | Set volume |
| `/loop` | Toggle loop mode |
| `/shuffle` | Shuffle queue |
| `/clear` | Clear upcoming queue |

## Prerequisites

- **Python 3.10+**
- **FFmpeg** installed and in PATH
- A Telegram **Bot Token** (from [@BotFather](https://t.me/BotFather))
- A Telegram **API ID & Hash** (from [my.telegram.org](https://my.telegram.org))
- A **User Account** session string (for the userbot that joins VCs)

## Installation

### 1. Clone & Install

```bash
git clone https://github.com/your-repo/Music-Bot.git
cd Music-Bot
pip install -r requirements.txt
```

### 2. Install FFmpeg

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install ffmpeg -y
```

**Windows:**
1. Download from [ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extract and add the `bin` folder to your system PATH
3. Verify: `ffmpeg -version`

**macOS:**
```bash
brew install ffmpeg
```

### 3. Generate Session String

```bash
python session_generator.py
```

This will ask for:
1. Your `API_ID`
2. Your `API_HASH`
3. Your phone number
4. The verification code sent to your Telegram

It outputs a `SESSION_STRING` — copy it for the next step.

> ⚠️ **Never share your session string** — it grants full access to your Telegram account.

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
API_ID=12345678
API_HASH=your_api_hash_here
BOT_TOKEN=123456:ABC-DEF1234...
SESSION_STRING=your_session_string_here
SUDO_USERS=123456789
```

### 5. Run

```bash
python main.py
```

## Usage

1. Add the **bot** to a Telegram group
2. Add the **userbot account** to the same group (or make it admin)
3. Start a **voice chat** in the group
4. Send `/play <song name or YouTube URL>`

## Deployment (Linux VPS)

### Using systemd

Create `/etc/systemd/system/musicbot.service`:

```ini
[Unit]
Description=Telegram Music Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/Music-Bot
ExecStart=/usr/bin/python3 main.py
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable musicbot
sudo systemctl start musicbot
sudo systemctl status musicbot    # Check status
journalctl -u musicbot -f         # View logs
```

### Using screen (quick)

```bash
screen -S musicbot
python main.py
# Ctrl+A, D to detach
# screen -r musicbot to reattach
```

## Architecture

```
User sends /play ──→ Bot (Pyrogram) ──→ yt-dlp extracts URL
                                         │
                                         ▼
                                   QueueManager
                                         │
                                         ▼
                              StreamManager (PyTgCalls)
                                         │
                                         ▼
                              Userbot joins VC & streams
                              via FFmpeg audio/video pipe
```

## Troubleshooting

| Issue | Solution |
|---|---|
| `No module named 'pytgcalls'` | Run `pip install py-tgcalls[pyrogram]` |
| Bot doesn't play audio | Ensure FFmpeg is installed: `ffmpeg -version` |
| Userbot can't join VC | Add the userbot account to the group with permission |
| `FloodWait` errors | Wait the specified time; avoid rapid commands |
| `SESSION_STRING` invalid | Regenerate with `python session_generator.py` |

## License

MIT
