# 🚀 TEL2BALE — Telegram to Bale Bridge Bot

<div align="center">

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
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
- Database access is non-blocking (`aiosqlite`) with in-memory RAM caching and optional **Redis** state storage for maximum throughput.

---

## ✨ Features

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
- **3-Way Security Captcha Challenge**:
  - Independent admin toggles for Ticket submission, Poll voting, and File forwarding.
  - Advanced distorted sinusoidal image captcha with automatic timeout and refresh limit.
- **Admin Control Panel**:
  - Native Reply Keyboard buttons with Telegram user/chat pickers.
  - Whitelist mode toggle, ban/unban by Telegram ID or Bale ID.
  - Global and per-user download volume quotas.
  - Registration limits (total users and active users capacity).
  - Mandatory channel join enforcement with public/private link resolution.
  - Database backup file export directly inside Telegram chat.
  - Live donation link customization.
- **Containerized & Automated**: Production-ready `Dockerfile`, `docker-compose.yml`, and one-line setup scripts.

---

## 📋 Prerequisites & Tokens

1. **Telegram API ID & API Hash**: Obtain from [my.telegram.org](https://my.telegram.org).
2. **Telegram Bot Token**: Create a bot via [@BotFather](https://t.me/BotFather) on Telegram.
3. **Bale Bot Token**: Create a bot via Bale's BotFather and obtain the token.
4. **Arvan Cloud S3 (Optional for files > 20MB)**: S3 Access Key, Secret Key, and Endpoint URL.

---

## 🚀 Installation & Deployment Methods

You can deploy the bot using **Docker** (recommended) or **Native Linux/Windows** environments.

---

### Method 1: Automated 1-Line Docker Deployment (Fastest) 🐳

If your Linux server does not have Docker or Docker Compose installed yet, this script will automatically install Docker Engine, download the source code, configure `.env`, and start the containers:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/thehornet2002/tel2bale/main/setup_docker.sh)
```

If not logged in as root:
```bash
sudo -i
bash <(curl -Ls https://raw.githubusercontent.com/thehornet2002/tel2bale/main/setup_docker.sh)
```

---

### Method 2: Manual Docker Compose

If Docker and Docker Compose are already installed on your server:

```bash
# 1. Clone repository
git clone https://github.com/thehornet2002/tel2bale.git
cd tel2bale

# 2. Configure environment file
cp example.env .env
nano .env

# 3. Build and run in background
docker compose up -d --build
```

**Helpful Container Management Commands:**
```bash
docker compose logs -f       # View live logs
docker compose ps            # Check container status
docker compose restart       # Restart bot container
docker compose down          # Stop containers
```

Persistent volumes for `bot.db`, `logs`, `backups`, and `downloads` are mapped to the host directory automatically.

---

### Method 3: Automated 1-Line Native Linux Setup (Without Docker)

Installs system dependencies, Python virtual environment, dependencies, `.env` file, and configures a `systemd` background service:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/thehornet2002/tel2bale/main/setup.sh)
```

---

### Method 4: Manual Native Linux Setup (Systemd Service)

#### 1. Install System Packages
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-dev build-essential libjpeg-dev zlib1g-dev git
```

#### 2. Clone and Setup Virtual Environment
```bash
git clone https://github.com/thehornet2002/tel2bale.git
cd tel2bale

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

#### 3. Configure Environment Variables
```bash
cp example.env .env
nano .env
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

Paste configuration (adjust `/root/tel2bale` path if necessary):
```ini
[Unit]
Description=Tel2Bale Bridge Bot Daemon
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/tel2bale
ExecStart=/root/tel2bale/.venv/bin/python /root/tel2bale/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tel2bale
```

**Service Commands:**
```bash
sudo systemctl status tel2bale     # Service status
sudo systemctl restart tel2bale    # Restart service
sudo journalctl -u tel2bale -f     # Live journal logs
```

---

### Method 5: Windows (Local Testing & Development)

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

# Redis Configuration (Optional for state acceleration)
REDIS_URL=redis://127.0.0.1:6379/0

# Optional Telegram Proxy
TEL_PROXY_SCHEME=
TEL_PROXY_HOST=
TEL_PROXY_PORT=

# Optional Bale Proxy
BALE_PROXY=
```

### Configuration Parameters

| Variable | Default | Description |
|---|---|---|
| `TEL_API_ID` | Required | Telegram API ID from my.telegram.org |
| `TEL_API_HASH` | Required | Telegram API Hash from my.telegram.org |
| `TEL_BOT_TOKEN` | Required | Telegram Bot Token from @BotFather |
| `TEL_ADMIN_IDS` | Required | Comma-separated Telegram user IDs of administrators |
| `TEL_WHITELIST_ENABLED` | `False` | Enable bot access whitelist mode on startup |
| `TEL_WHITELIST_USERS` | - | Seed list of allowed Telegram user IDs |
| `TEL_MAX_FILE_SIZE` | `20` | Max file size in MB for direct Bale upload |
| `MAX_USERS` | `0` | Max total registered users allowed (0 = unlimited) |
| `MAX_ACTIVE_USERS` | `0` | Max users with Bale ID/token allowed (0 = unlimited) |
| `SUPPORT_MESSAGE_LIMIT` | `5` | Maximum pending unanswered tickets allowed per user |
| `REDIS_URL` | - | Optional Redis connection string (e.g. `redis://127.0.0.1:6379/0`) |
| `DONATION_LINK` | - | Custom donation URL displayed on start keyboard |
| `BALE_PROXY` | - | Optional proxy URL for Bale API communication |

---

## 📂 Project Directory Structure

```text
tel2bale/
├── Dockerfile                   # Optimized python:3.12-slim container image
├── docker-compose.yml           # Multi-container Compose configuration with volumes
├── setup_docker.sh              # 1-line automated Docker deployment script
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
│           └── user_handler.py
│
├── services/
│   ├── bale_service.py          # Bale API client with retry mechanism and binary handling
│   ├── s3_service.py            # Arvan Cloud S3 integration and presigned URL generation
│   ├── quota_service.py         # Atomic download quota verification and rollback
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
- 🔐 **Captcha Settings**: Toggle anti-spam image captchas individually for Tickets, Polls, and File uploads.
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

The project includes an integrated verification test covering URL parsing, anti-SSRF checks, quota reservation, database transactions, whitelist rules, Redis connectivity, and captcha generation:

```bash
python tests/test_self_check.py
```

---

## 📜 License

This project is licensed under the **[MIT License](LICENSE)**.
