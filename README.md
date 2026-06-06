---

title: Telegram Music Bot
emoji: 🎵
colorFrom: purple
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
-------------

# 🎵 Telegram VC Music Bot

<p align="center">
  <img src="catforg.jpeg" width="220" alt="Telegram Music Bot">
</p>

<h3 align="center">
High-Performance Telegram Voice Chat Music & Video Streaming Bot
</h3>

<p align="center">
Built with Pyrogram • PyTgCalls • FFmpeg • yt-dlp
</p>

<p align="center">
Stream music and videos directly into Telegram Voice Chats with queue management, looping, volume controls, and Docker deployment support.
</p>

---

## ⭐ Features At A Glance

* 🎵 YouTube Music Playback
* 🎥 Video Streaming
* 📋 Smart Queue System
* 🔄 Loop & Shuffle Support
* 🔊 Volume Controls
* 🐳 Docker Ready
* 🖥 VPS Ready
* ⚡ Lightweight & Fast

---

## ✨ Features

### 🎶 Music Streaming

* Play music from YouTube URLs
* Search songs by name
* High-quality audio playback
* Fast extraction using yt-dlp
* Automatic queue progression

### 🎥 Video Streaming

* Stream YouTube videos directly in Voice Chats
* Supports URLs and search queries
* Smooth playback via FFmpeg

### 📋 Queue Management

* Per-chat queue system
* Automatic next-track playback
* View current queue
* Shuffle queue
* Clear queue

### 🎛 Playback Controls

* Pause & Resume
* Skip tracks
* Stop playback
* Leave Voice Chat
* Loop current song
* Loop entire queue

### 🔊 Audio Controls

* Adjustable volume (1–200%)
* Real-time volume updates

### 🚀 Production Ready

* Docker deployment
* VPS deployment
* Systemd support
* Automatic restart support
* Optimized architecture

---

## 📜 Commands

| Command              | Description                |
| -------------------- | -------------------------- |
| `/play <song/url>`   | Play audio in voice chat   |
| `/vplay <video/url>` | Play video in voice chat   |
| `/skip`              | Skip current track         |
| `/pause`             | Pause playback             |
| `/resume`            | Resume playback            |
| `/stop`              | Stop playback and leave VC |
| `/queue`             | Show current queue         |
| `/volume <1-200>`    | Set playback volume        |
| `/loop`              | Toggle loop mode           |
| `/shuffle`           | Shuffle queue              |
| `/clear`             | Clear upcoming tracks      |

---

## 📁 Project Structure

```text
tg-music-bot/
├── player/
├── utils/
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── bot.py
├── config.py
├── main.py
├── requirements.txt
├── session_generator.py
├── userbot.py
└── catforg.jpeg
```

---

## 🛠 Requirements

* Python 3.10+
* FFmpeg
* Telegram Bot Token
* Telegram API ID
* Telegram API Hash
* Telegram User Session String

---

## ⚡ Quick Start

### Clone Repository

```bash
git clone https://github.com/stack-rishi/tg-music-bot.git
cd tg-music-bot
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment

Create a `.env` file:

```env
API_ID=12345678
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
SESSION_STRING=your_session_string
SUDO_USERS=123456789
```

### Start Bot

```bash
python main.py
```

---

## 🔑 Generate Session String

Run:

```bash
python session_generator.py
```

You'll be prompted for:

* API ID
* API Hash
* Phone Number
* Telegram Verification Code

After successful login, copy the generated:

```text
SESSION_STRING
```

> ⚠️ Never share your SESSION_STRING. It provides access to your Telegram account.

---

## 🎬 Installing FFmpeg

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install ffmpeg -y
```

### macOS

```bash
brew install ffmpeg
```

### Windows

1. Download FFmpeg
2. Extract the archive
3. Add the `bin` folder to your PATH

Verify installation:

```bash
ffmpeg -version
```

---

## 📖 Usage

1. Add the bot to your Telegram group.
2. Add the userbot account to the same group.
3. Grant required permissions.
4. Start a Voice Chat.
5. Use:

```text
/play Faded
```

or

```text
/play https://youtube.com/watch?v=...
```

---

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t tg-music-bot .
```

### Run Container

```bash
docker run -d \
  --name tg-music-bot \
  --env-file .env \
  tg-music-bot
```

---

## 🖥 VPS Deployment

Create:

```text
/etc/systemd/system/musicbot.service
```

```ini
[Unit]
Description=Telegram Music Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/tg-music-bot
ExecStart=/usr/bin/python3 main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable Service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable musicbot
sudo systemctl start musicbot
```

View Status:

```bash
sudo systemctl status musicbot
```

View Logs:

```bash
journalctl -u musicbot -f
```

---

## 🏗 Architecture

```text
User
 │
 ▼
Telegram Bot (Pyrogram)
 │
 ▼
yt-dlp
 │
 ▼
Queue Manager
 │
 ▼
Stream Manager
 │
 ▼
PyTgCalls
 │
 ▼
Telegram Voice Chat
```

---

## 🔧 Troubleshooting

| Issue                     | Solution                          |
| ------------------------- | --------------------------------- |
| No module named pytgcalls | Install `py-tgcalls[pyrogram]`    |
| FFmpeg not found          | Install FFmpeg and add it to PATH |
| Userbot cannot join VC    | Add userbot and grant permissions |
| FloodWait errors          | Wait for Telegram cooldown        |
| Invalid SESSION_STRING    | Generate a new session string     |

---

## 🤝 Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push your branch
5. Open a Pull Request

---

## 🙏 Credits

* Pyrogram
* PyTgCalls
* yt-dlp
* FFmpeg

---

## 📄 License

Licensed under the MIT License.

---

<p align="center">
Made with ❤️ for Telegram Voice Chats
</p>
