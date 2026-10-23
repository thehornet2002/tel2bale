#!/bin/bash

set -e

# Terminal Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   🚀 TEL2BALE — Native Setup & Deploy  ${NC}"
echo -e "${GREEN}========================================${NC}"

# 0. Check for root privileges
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}❌ Error: Please run this script with root (sudo) privileges${NC}"
  echo -e "${YELLOW}Usage: sudo bash setup.sh${NC}"
  exit 1
fi

SERVICE_NAME="tel2bale"
GITHUB_REPO="thehornet2002/tel2bale"

# ==========================================
# 1. Prepare Directory & Fetch Source
# ==========================================
echo -e "\n${YELLOW}Step 1: Preparing directory and fetching source code...${NC}"

if [ -f "main.py" ] && [ -f "requirements.txt" ]; then
    APP_DIR="$(pwd)"
    echo -e "${GREEN}✓ Running inside project directory: $APP_DIR${NC}"
else
    APP_DIR="/root/tel2bale"
    mkdir -p "$APP_DIR"
    cd "$APP_DIR"
    if [ -d ".git" ]; then
        echo -e "${BLUE}Updating existing repository...${NC}"
        git pull origin main 2>/dev/null || true
    else
        echo -e "${BLUE}Cloning repository from GitHub...${NC}"
        apt-get update -qq 2>/dev/null || true
        apt-get install -y -qq git curl jq 2>/dev/null || apt-get install -y git curl jq
        git clone "https://github.com/$GITHUB_REPO.git" "$APP_DIR" 2>/dev/null || {
            echo -e "${YELLOW}Git clone failed, downloading release archive...${NC}"
            curl -sSL "https://github.com/$GITHUB_REPO/archive/refs/heads/main.tar.gz" | tar -xz --strip-components=1 -C "$APP_DIR"
        }
    fi
fi

cd "$APP_DIR"
mkdir -p logs backups downloads cookies

# ==========================================
# 2. Install System Dependencies & Tools
# ==========================================
echo -e "\n${YELLOW}Step 2: Installing system packages and development libraries...${NC}"
apt-get update -qq 2>/dev/null || apt-get update
apt-get install -y build-essential gcc python3 python3-venv python3-dev \
    libjpeg-dev zlib1g-dev ffmpeg ca-certificates curl jq git redis-server 2>/dev/null || {
    echo -e "${YELLOW}Retrying package installation...${NC}"
    apt-get update && apt-get install -y build-essential gcc python3 python3-venv python3-dev \
        libjpeg-dev zlib1g-dev ffmpeg ca-certificates curl jq git redis-server
}
echo -e "${GREEN}✓ System dependencies installed successfully.${NC}"

# ==========================================
# 3. Configure, Harden & Start Redis Server
# ==========================================
echo -e "\n${YELLOW}Step 3: Configuring, detecting, and hardening Redis Server...${NC}"

# Ensure redis-server package is installed
if ! command -v redis-server &>/dev/null && ! command -v redis-cli &>/dev/null; then
    echo -e "${BLUE}Installing redis-server package...${NC}"
    apt-get install -y redis-server 2>/dev/null || apt-get install -y redis 2>/dev/null || true
fi

# Hardening against CVE-2025-49844 (Disable unused Lua scripting execution)
if [ -f "/etc/redis/redis.conf" ]; then
    grep -q "rename-command EVAL " /etc/redis/redis.conf || echo 'rename-command EVAL ""' >> /etc/redis/redis.conf
    grep -q "rename-command EVALSHA " /etc/redis/redis.conf || echo 'rename-command EVALSHA ""' >> /etc/redis/redis.conf
    grep -q "rename-command SCRIPT " /etc/redis/redis.conf || echo 'rename-command SCRIPT ""' >> /etc/redis/redis.conf
fi

systemctl enable --now redis-server 2>/dev/null || systemctl enable --now redis 2>/dev/null || true

# Test local Redis connectivity
if redis-cli ping 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}✓ Local Redis server is installed, running, and responding to PING (127.0.0.1:6379).${NC}"
    DEFAULT_REDIS_URL="redis://127.0.0.1:6379/0"
else
    echo -e "${YELLOW}Notice: Local Redis starting or using custom port/password.${NC}"
    DEFAULT_REDIS_URL="redis://127.0.0.1:6379/0"
fi

# ==========================================
# 4. Virtual Environment & Python Packages
# ==========================================
echo -e "\n${YELLOW}Step 4: Setting up Python virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
echo -e "${BLUE}Upgrading pip and wheel...${NC}"
pip install --upgrade pip setuptools wheel -q

echo -e "${BLUE}Installing requirements.txt (including yt-dlp, kurigram, Pillow, etc.)...${NC}"
pip install -r requirements.txt
deactivate
echo -e "${GREEN}✓ Python packages installed successfully.${NC}"

# ==========================================
# 5. Configure .env Environment File
# ==========================================
echo -e "\n${YELLOW}Step 5: Configuring environment variables (.env)...${NC}"
if [ -f ".env" ]; then
    echo -e "${CYAN}.env file already exists.${NC}"
    read -p "Do you want to reconfigure it? (y/N): " RECONFIG
    RECONFIG=${RECONFIG:-n}
else
    RECONFIG="y"
fi

if [[ "$RECONFIG" =~ ^[Yy]$ ]]; then
    read -p "Enter TEL_API_ID: " INPUT_API_ID
    read -p "Enter TEL_API_HASH: " INPUT_API_HASH
    read -p "Enter TEL_BOT_TOKEN: " INPUT_BOT_TOKEN
    read -p "Enter TEL_ADMIN_IDS (comma-separated): " INPUT_ADMIN_IDS

    echo ""
    read -p "Enter TEL_MAX_FILE_SIZE (MB) [Default: 20]: " INPUT_MAX_FILE_SIZE
    INPUT_MAX_FILE_SIZE=${INPUT_MAX_FILE_SIZE:-20}

    read -p "Enter DONATION_LINK [Default: https://daramet.com/Hornet2002]: " INPUT_DONATION
    INPUT_DONATION=${INPUT_DONATION:-https://daramet.com/Hornet2002}

    echo ""
    read -p "Enter REDIS_URL [Default: ${DEFAULT_REDIS_URL:-redis://127.0.0.1:6379/0}]: " INPUT_REDIS_URL
    INPUT_REDIS_URL=${INPUT_REDIS_URL:-${DEFAULT_REDIS_URL:-redis://127.0.0.1:6379/0}}

    cat <<EOF > .env
TEL_API_ID=$INPUT_API_ID
TEL_API_HASH=$INPUT_API_HASH
TEL_BOT_TOKEN=$INPUT_BOT_TOKEN
TEL_ADMIN_IDS=$INPUT_ADMIN_IDS

TEL_START_TXT="به ربات انتقال پیام تلگرام به بله خوش آمدید."
TEL_HELP_TXT="ابتدا شناسه بله و توکن ربات بله خود را تنظیم کنید، سپس پیام‌ها را ارسال کنید."

TEL_ADS_CHANNELS=
TEL_MAX_FILE_SIZE=$INPUT_MAX_FILE_SIZE
TEL_IN_MEMORY=False

DONATION_LINK=$INPUT_DONATION
SUPPORT_MESSAGE_LIMIT=5

MAX_USERS=0
MAX_ACTIVE_USERS=0

REDIS_URL=$INPUT_REDIS_URL

# TEL_PROXY_SCHEME=socks5
# TEL_PROXY_HOST=127.0.0.1
# TEL_PROXY_PORT=2080
# BALE_PROXY=
EOF
    echo -e "${GREEN}✓ .env file created successfully.${NC}"
fi

# ==========================================
# 6. Create & Start Systemd Service
# ==========================================
echo -e "\n${YELLOW}Step 6: Setting up systemd background service...${NC}"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=Tel2Bale Telegram to Bale Bridge Bot Daemon
After=network.target redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/python $APP_DIR/main.py
Restart=always
RestartSec=5
StartLimitIntervalSec=0
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME" >/dev/null 2>&1

echo -e "${BLUE}Starting service $SERVICE_NAME...${NC}"
systemctl restart "$SERVICE_NAME"

echo -e "\n${GREEN}════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Installation & Startup completed successfully!  ${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"

echo -e "\n${CYAN}Helpful management commands:${NC}"
echo -e "🔹 Check status:      ${YELLOW}systemctl status $SERVICE_NAME${NC}"
echo -e "🔹 View live logs:    ${YELLOW}journalctl -u $SERVICE_NAME -f${NC}"
echo -e "🔹 Restart bot:       ${YELLOW}systemctl restart $SERVICE_NAME${NC}"
echo -e "🔹 Stop bot:          ${YELLOW}systemctl stop $SERVICE_NAME${NC}"
