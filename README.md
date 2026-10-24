# 🚀 TEL2BALE — Telegram to Bale Bridge Bot

<div align="center">

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org)
[![Redis](https://img.shields.io/badge/Redis-Supported-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)](https://github.com/thehornet2002/tel2bale)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**A high-performance, asynchronous bridge bot transferring messages and media from Telegram to Bale messenger.**

</div>

---

## 📌 Overview

**TEL2BALE** is a fully asynchronous, non-blocking bridge bot designed to forward messages, media, and documents from **Telegram** to the **Bale** messenger.

It is particularly valuable in environments where direct access to Telegram is restricted or limited. Users can send their texts, photos, videos, voices, or large files to the Telegram bot, which securely and automatically delivers them to the configured Bale destination.

### Media Forwarding Workflow:
- Files smaller than or equal to `TEL_MAX_FILE_SIZE` (default 20MB) are directly uploaded and sent to Bale API.
- Files exceeding this threshold are uploaded to **Arvan Cloud S3-compatible object storage**, and an expiring presigned download link is sent to the Bale destination.
- User bandwidth is strictly managed through an atomic SQLite/database quota reservation system.
- Database access is non-blocking (`aiosqlite`) with in-memory RAM caching and **Redis** state storage for maximum throughput.

---

## ✨ Features

- **Multimedia Downloader Engine**:
  - **YouTube**: Download videos and shorts with selectable resolutions (1080p, 720p, 480p, 360p) or extract audio (MP3).
  - **Instagram**: Seamless download of Reels, Posts, and IGTV.
  - **Spotify**: Fast track metadata extraction and high-quality MP3 audio download.
  - **Strict Domain Protection**: Strict allowlist limiting connections to authorized official domains with anti-SSRF protections.
- **Global Cookie Management**:
  - Admin `cookies.txt` support with 0600 file permissions for overcoming age-restrictions and bot-detection challenges.
- **Enhanced Quota & Bandwidth Management**:
  - Atomic per-user download volume accounting across direct files and streaming downloads.
  - User self-service quota inspection (`📊 سهمیه مصرفی من`).
  - Automatic offloading to S3 when media exceeds `TEL_MAX_FILE_SIZE`.
- **Rich Media Forwarding**: Supports text, photos, videos, audio, voice messages, documents, animations (GIFs), locations, and contacts.
- **Large File S3 Storage**: Streaming upload with automatic unique UUID naming, temporary presigned links, bucket capacity recovery, and immediate disk cleanup.
- **Redis State Management**: High-speed user session state caching with automatic fallback to RAM and SQLite.
- **Advanced Ticketing System (Senfi-style)**:
  - Custom categories with normal or anonymous modes.
  - Dedicated user ticket view and history (`My Tickets`).
  - Native admin management panel with status filters (Pending, Answered, All), pagination, and direct in-bot replies.
- **Multi-Poll & Survey System**:
  - Create and manage multiple active polls with custom questions and choices.
  - One-vote-per-user enforcement with live percentage and visual bar charts.
- **5-Level Security Image Captcha Challenge**:
  - Dynamic mathematical/visual captcha with 5 difficulty levels (Very Easy to Very Hard).
  - Customizable character length (4 to 10 characters).
  - 20-minute temporary lockout upon 5 consecutive failed or expired challenges.
  - Interactive InlineKeyboardMarkup admin control panel.
- **Admin Control Panel**:
  - Native Reply Keyboard buttons with Telegram user/chat pickers.
  - Whitelist mode toggle, ban/unban by Telegram ID or Bale ID.
  - Global and per-user download volume quotas.
  - Registration limits (total users and active users capacity).
  - Cookie file upload and deletion.
  - Mandatory channel join enforcement with public/private link resolution.
  - Database backup file export directly inside Telegram chat.
  - Live donation link customization.

---

## 📋 Prerequisites & Tokens

1. **Telegram API ID & API Hash**: Obtain from [my.telegram.org](https://my.telegram.org).
2. **Telegram Bot Token**: Create a bot via [@BotFather](https://t.me/BotFather) on Telegram.
3. **Bale Bot Token**: Create a bot via Bale's BotFather and obtain the token.
4. **Arvan Cloud S3 (Optional for files > 20MB)**: S3 Access Key, Secret Key, and Endpoint URL.

---

## 🚀 Installation & Deployment

---

### Method 1: Automated 1-Line Native Linux Setup (Recommended)

This automated setup script installs Python, system libraries (`ffmpeg`, `build-essential`, `libjpeg-dev`, `redis-server`), configures the virtual environment, installs dependencies, sets up `.env`, and enables a persistent `systemd` background service:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/thehornet2002/tel2bale/main/setup.sh)
```

If not logged in as root:
```bash
sudo -i
bash <(curl -Ls https://raw.githubusercontent.com/thehornet2002/tel2bale/main/setup.sh)
```

---

### Method 2: Manual Native Linux Setup (Systemd Service)

#### 1. Install System Packages & Redis
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-dev build-essential gcc \
    libjpeg-dev zlib1g-dev ffmpeg ca-certificates curl jq git redis-server
sudo systemctl enable --now redis-server
```

#### 2. Clone Repository & Setup Virtual Environment
```bash
sudo useradd --system --no-create-home --shell /usr/sbin/nologin tel2bale 2>/dev/null || true
sudo mkdir -p /opt/tel2bale
sudo git clone https://github.com/thehornet2002/tel2bale.git /opt/tel2bale
cd /opt/tel2bale

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

#### 3. Configure Environment Variables
```bash
cp example.env .env
nano .env
sudo chown -R tel2bale:tel2bale /opt/tel2bale
sudo chmod 600 /opt/tel2bale/.env
```

#### 4. Test Run
```bash
python main.py
```

#### 5. Configure Systemd Service
Create service file `/etc/systemd/system/tel2bale.service`:
```bash
sudo nano /etc/systemd/system/tel2bale.service
```

Paste configuration:
```ini
[Unit]
Description=Tel2Bale Telegram to Bale Bridge Bot Daemon
After=network.target redis-server.service

[Service]
Type=simple
User=tel2bale
Group=tel2bale
WorkingDirectory=/opt/tel2bale
ExecStart=/opt/tel2bale/.venv/bin/python /opt/tel2bale/main.py
Restart=always
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/tel2bale/bot.db /opt/tel2bale/downloads /opt/tel2bale/backups /opt/tel2bale/cookies /opt/tel2bale/logs

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tel2bale
```

**Service Management Commands:**
```bash
sudo systemctl status tel2bale     # Check service status
sudo systemctl restart tel2bale    # Restart service
sudo journalctl -u tel2bale -f     # View live logs
```

---

### Method 3: Windows (Local Testing & Development)

Run inside PowerShell:
```powershell
git clone https://github.com/thehornet2002/tel2bale.git
cd tel2bale

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

copy example.env .env
notepad .env

python main.py
```

---

## ⚙️ Environment Variables (`.env`)

```env
# Telegram Bot Configuration
TEL_API_ID=1234567
TEL_API_HASH=abcdef0123456789abcdef0123456789
TEL_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TEL_ADMIN_IDS=123456789,987654321

# Bot Welcome and Help Messages
TEL_START_TXT=به ربات انتقال پیام تلگرام به بله خوش آمدید.
TEL_HELP_TXT=ابتدا شناسه بله و توکن ربات بله خود را تنظیم کنید، سپس پیام‌ها را ارسال کنید.

# Whitelist Configuration
TEL_WHITELIST_ENABLED=False
TEL_WHITELIST_USERS=123456789,111222333

# File Limits & Quota
TEL_ADS_CHANNELS=
TEL_MAX_FILE_SIZE=20
TEL_IN_MEMORY=False
DONATION_LINK=https://daramet.com/Hornet2002
SUPPORT_MESSAGE_LIMIT=5

# Registration & Capacity Limits (0 = Unlimited)
MAX_USERS=0
MAX_ACTIVE_USERS=0

# Redis Configuration (Mandatory)
REDIS_URL=redis://127.0.0.1:6379/0

# Optional Cloudflare Turnstile Captcha
# CF_TURNSTILE_SITE_KEY=0x4AAAAAA...
# CF_TURNSTILE_SECRET_KEY=0x4AAAAAA...
# CF_TURNSTILE_DOMAIN=https://captcha.yourdomain.com

# Optional Telegram Proxy
# TEL_PROXY_SCHEME=
# TEL_PROXY_HOST=
# TEL_PROXY_PORT=

# Optional Bale Proxy
# BALE_PROXY=
```

---

## 📂 Project Directory Structure

```text
tel2bale/
├── setup.sh                     # 1-line automated native Linux systemd setup script
├── main.py                      # Bot entry point, startup procedures, and command setup
├── config.py                    # Environment management with async locking and validation
├── requirements.txt             # Python package dependencies
├── example.env                  # Template environment variables
│
├── db/
│   ├── db_async.py              # Asynchronous SQLite connection manager
│   ├── model_async.py           # Core database models, schema initialization, and queries
│   ├── redis_client.py          # Asynchronous Redis client with automatic RAM fallback
│   └── backup.py                # Database backup utility
│
├── handlers/
│   ├── commands.py              # Handlers for /start, /help, and /panel commands
│   ├── callback.py              # Inline callback query router with strict access control
│   ├── messages.py              # Main message dispatcher and input state processor
│   └── handler_helpers/
│       ├── command_helper.py
│       ├── callback_helpers/
│       │   ├── navigation_handler.py
│       │   ├── user_handler.py
│       │   └── admin/       # Management controllers (tickets, polls, whitelist, limits, etc.)
│       └── message_helpers/
│           ├── admin_handler.py
│           ├── forward_handler.py
│           ├── captcha_handler.py
│           ├── media_handler.py
│           └── user_handler.py
│
├── services/
│   ├── bale_service.py          # Bale API client with retry mechanism and binary handling
│   ├── s3_service.py            # Arvan Cloud S3 integration and presigned URL generation
│   ├── quota_service.py         # Atomic download quota verification and rollback
│   ├── downloader_service.py    # Multi-platform media downloader (YouTube, Spotify, Instagram)
│   ├── cookie_service.py        # Global Netscape cookies manager
│   ├── turnstile_service.py     # Cloudflare Turnstile verification integration
│   └── captcha_service.py       # High-security sinusoidal distorted image captcha engine
│
├── utils/
│   ├── filters.py               # Custom Pyrogram filters (whitelist, user capacity, join ads)
│   ├── keyboards.py             # Inline and Reply keyboard builders
│   ├── logger.py                # Rotating log handler
│   └── parser.py                # URL validation with anti-SSRF protections
│
└── tests/
    └── test_self_check.py       # Comprehensive internal test and security validation suite
```

---

## 🛠️ Admin Panel Capabilities

Administrators can access the management panel at any time by sending `/admin` or `/panel` in private chat:

- 💾 **Database Backup**: Generates an SQLite database backup file and delivers it in Telegram chat.
- 🎫 **Support Tickets**: Browse tickets filtered by status (Pending, Answered, All), view details, and reply directly.
- 🗂 **Ticket Categories**: Add categories (Normal or Anonymous modes) and archive/delete them.
- 📊 **Polls Management**: Create surveys with custom questions and choices, open/close status, and inspect results.
- 🔐 **Captcha Settings**: Toggle image captchas individually for Tickets, Polls, File uploads, and Media downloads, plus Cloudflare domain/key configuration.
- 🍪 **Cookie Management**: Upload global `cookies.txt` for YouTube and Instagram bot bypass.
- 🛡️ **Whitelist System**: Restrict bot usage to approved users, add/remove IDs, or toggle whitelist enforcement.
- 🚫 **Ban & Unban**: Block users by Telegram ID or Bale ID using native user picker buttons.
- ➕/➖ **Administrator Management**: Promote or demote admins with persistent `.env` updating.
- 🌐/👤 **Bandwidth Quotas**: Set global or per-user download thresholds (in GB).
- 👥/🟢 **User Limits**: Restrict total registered users or active users with configured Bale tokens.
- 📢/✉️ **Broadcasting**: Send broadcast messages to all users or direct messages to a specific user.
- 🔗/❌ **Mandatory Channel Join**: Add and remove required Telegram channel subscriptions.
- ☕ **Donation Link**: Update the donation link live from the bot interface.

---

## 🧪 Testing & Verification

Run the test suite:
```bash
python tests/test_self_check.py
```

---

## 📜 License

Distributed under the **[MIT License](LICENSE)**.
