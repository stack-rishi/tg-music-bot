<div align="center">

# 🎵 GlissStream Telegram VC Bot

[![Try the Bot](https://img.shields.io/badge/Telegram-Try%20The%20Bot%20🚀-blue?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/ChatpataAlooBot)
[![GitHub Stars](https://img.shields.io/github/stars/stack-rishi/tg-music-bot?style=for-the-badge&color=ffd700)](https://github.com/stack-rishi/tg-music-bot/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/stack-rishi/tg-music-bot?style=for-the-badge&color=8a2be2)](https://github.com/stack-rishi/tg-music-bot/network/members)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/github/license/stack-rishi/tg-music-bot?style=for-the-badge&color=2ea44f)](LICENSE)
[![Support Group](https://img.shields.io/badge/Telegram-Support-26A69A?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/Ri5h11)

A state-of-the-art, high-performance Telegram Voice Chat music and video player bot. Seamlessly stream audio and video with instant startup, zero local disk footprint, and Spotify-tier audio quality.

[⚡ **Try the Live Bot on Telegram!** ⚡](https://t.me/ChatpataAlooBot)

[Report Bug](https://github.com/stack-rishi/tg-music-bot/issues/new?template=bug_report.md) · [Request Feature](https://github.com/stack-rishi/tg-music-bot/issues/new?template=feature_request.md)

</div>

---

## ⚡ Highlights & Key Advantages

*   🚀 **100% Direct HTTP Streaming**: Streams YouTube media directly to Telegram voice chats without downloading files locally. Disconnects disk usage concerns entirely and starts playback in **under 2 seconds**.
*   🔊 **Spotify-Tier Audio Quality**: Utilizes PyTgCalls `AudioQuality.HIGH` (48kHz stereo, maximum allowable WebRTC bitrate) for crystal-clear sound, avoiding muddy compression.
*   🎥 **HD Video Streaming**: Supports streaming HD video (up to 720p at 30fps) inside group calls with automatic hardware-friendly transcoding priorities.
*   🕹️ **Interactive Control Panel**: Controls streams directly with beautiful inline keyboard buttons (Play, Pause, Skip, Loop, Volume) without typing commands.
*   🛡️ **Premium Bypass Stack**: Includes a built-in Proof-of-Origin (PO) Token server, portable Node.js runtime, and JavaScript Signature challenge solver to bypass YouTube's anti-bot restrictions and 403 blocks.
*   ♻️ **Robust Fallback Engine**: If YouTube fails completely, automatically falls back to alternative streaming platforms (e.g., SoundCloud) to keep the music playing.

---

## 🎮 Command Console

| Command | Action | Inline Control Available |
| :--- | :--- | :---: |
| `/play <url/query>` | Stream high-fidelity audio in group VC | Yes |
| `/vplay <url/query>` | Stream HD video (720p) in group VC | Yes |
| `/skip` | Advance to the next track in queue | Yes |
| `/pause` | Suspend playback temporarily | Yes |
| `/resume` | Continue playback of the suspended stream | Yes |
| `/stop` | Terminate the stream and disconnect | Yes |
| `/queue` | View upcoming tracks and current mode | Yes |
| `/volume <1-200>` | Calibrate stream volume | No |
| `/loop` | Cycle loop settings (Single / Queue / Off) | Yes |
| `/shuffle` | Randomize upcoming tracks | Yes |
| `/clear` | Wipe the upcoming queue | No |

---

## 🚀 Quick Start & Installation

### 1. System Prerequisites
Before deploying, make sure you have:
*   **Python 3.10 or 3.11**
*   **FFmpeg** installed and added to your system's `PATH`.

### 2. Installation Steps
Clone the repository and install the dependencies:
```bash
git clone https://github.com/stack-rishi/tg-music-bot.git
cd tg-music-bot
pip install -r requirements.txt
```

### 3. Generate userbot session string
Run the interactive helper script on your local machine to authenticate the userbot client:
```bash
python session_generator.py
```
Copy the long `SESSION_STRING` printed at the end of the script.
> ⚠️ **IMPORTANT**: Never share your session string. Anyone who obtains it can fully control the corresponding Telegram account.

### 4. Configuration
Duplicate `.env.example` as `.env` and fill in your details:
```env
API_ID=12345678
API_HASH=your_api_hash_here
BOT_TOKEN=123456:ABC-DEF1234...
SESSION_STRING=your_session_string_here
SUDO_USERS=123456789
```

### 5. Launch the Bot
```bash
python main.py
```

---

## 🛠️ Deploying 24/7 on Linux VPS

### Option A: Using tmux (Easiest)
Create a persistent tmux session to run the bot in the background:
```bash
tmux new -s musicbot
source .venv/bin/activate
python main.py
# Press Ctrl+B, then D to detach safely from tmux
```
To re-attach later:
```bash
tmux attach -t musicbot
```

### Option B: Using systemd (Recommended for Production)
Create `/etc/systemd/system/musicbot.service`:
```ini
[Unit]
Description=GlissStream Telegram Music Bot
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/tg-music-bot
ExecStart=/home/ec2-user/tg-music-bot/.venv/bin/python3 main.py
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```
Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable musicbot
sudo systemctl start musicbot
```

---

## ⚙️ How It Works (Architecture)

```
User sends /play ──→ Bot (Pyrogram) ──→ yt-dlp Metadata Extraction
                                                     │
                                                     ▼
                                               QueueManager
                                                     │
                                                     ▼
                                          StreamManager (PyTgCalls)
                                                     │
                                                     ▼
                                          Userbot joins VC & streams
                                          via direct HTTP video/audio pipe
```

---

## 💡 Troubleshooting

*   **`No module named 'pytgcalls'`**: Install the library with Pyrogram bindings using `pip install py-tgcalls[pyrogram]`.
*   **Silence / Playback Fails**: Ensure `ffmpeg` and `ffprobe` are installed and in your environment variables.
*   **Userbot Won't Join Voice Chat**: Ensure that the userbot account is a member of the group and has the permission to "Post voice messages" or join the call.
*   **YouTube Throttling / 403**: The bot uses a Proof-of-Origin token provider. Keep the token provider server running (handled automatically on startup).

---

## 📜 License & Acknowledgments

This project is licensed under the **MIT License**.
Special thanks to the [PyTgCalls](https://github.com/Laky-64/PyTgCalls) and [yt-dlp](https://github.com/yt-dlp/yt-dlp) communities for making VC streaming possible.
