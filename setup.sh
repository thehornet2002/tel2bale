#!/bin/bash

# ==============================================================================
#   🚀 TEL2BALE — Automated Native Setup & Deployment Script
#   Production-grade, zero-friction installer for Ubuntu/Debian Linux
# ==============================================================================

set -e

# Disable interactive debconf prompts
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a

# Terminal Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}${BOLD}   🚀 TEL2BALE — Native Linux Setup & Deployment    ${NC}"
echo -e "${GREEN}====================================================${NC}"

# 0. Check for root privileges
if [ "$EUID" -ne 0 ]; then
  echo -e "\n${RED}❌ Error: This script must be run with root (sudo) privileges.${NC}"
  echo -e "${YELLOW}Please run:${NC} ${BOLD}sudo -i${NC} ${YELLOW}and then rerun the script.${NC}"
  exit 1
fi

SERVICE_NAME="tel2bale"
GITHUB_REPO="thehornet2002/tel2bale"

# ==============================================================================
# 1. Prepare Directory & Fetch Latest Source Code
# ==============================================================================
echo -e "\n${YELLOW}Step 1: Preparing workspace and fetching source code...${NC}"

if [ -f "main.py" ] && [ -f "requirements.txt" ]; then
    APP_DIR="$(pwd)"
    echo -e "${GREEN}✓ Detected existing project directory: $APP_DIR${NC}"
    if [ -d ".git" ]; then
        echo -e "${BLUE}Fetching latest git commits...${NC}"
        git pull origin main 2>/dev/null || true
    fi
else
    APP_DIR="/opt/tel2bale"
    mkdir -p "$APP_DIR"
    cd "$APP_DIR"
    if [ -d ".git" ]; then
        echo -e "${BLUE}Updating existing repository at $APP_DIR...${NC}"
        git pull origin main 2>/dev/null || true
    else
        echo -e "${BLUE}Cloning repository from GitHub...${NC}"
        apt-get update -qq 2>/dev/null || true
        apt-get install -y -qq git curl jq 2>/dev/null || apt-get install -y git curl jq
        if ! git clone "https://github.com/$GITHUB_REPO.git" "$APP_DIR" 2>/dev/null; then
            echo -e "${YELLOW}Git clone failed, downloading release archive...${NC}"
            curl --fail --show-error --location "https://github.com/$GITHUB_REPO/archive/refs/heads/main.tar.gz" | tar -xz --strip-components=1 -C "$APP_DIR"
        fi
    fi
fi

cd "$APP_DIR"
mkdir -p logs backups downloads cookies

# ==============================================================================
# 2. Install System Packages & Media Libraries
# ==============================================================================
echo -e "\n${YELLOW}Step 2: Installing system dependencies and media tools...${NC}"
echo -e "${BLUE}Installing Python 3, build tools, ffmpeg, image libraries, and Redis...${NC}"

apt-get update -qq 2>/dev/null || apt-get update
apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3 \
    python3-venv \
    python3-dev \
    python3-pip \
    libjpeg-dev \
    zlib1g-dev \
    ffmpeg \
    ca-certificates \
    curl \
    jq \
    git \
    redis-server 2>/dev/null || {
    echo -e "${YELLOW}Retrying package installation with apt-get update...${NC}"
    apt-get update && apt-get install -y \
        build-essential gcc python3 python3-venv python3-dev python3-pip \
        libjpeg-dev zlib1g-dev ffmpeg ca-certificates curl jq git redis-server
}

echo -e "${GREEN}✓ System dependencies and media libraries installed.${NC}"

# ==============================================================================
# 3. Configure, Harden, and Verify Redis Server
# ==============================================================================
echo -e "\n${YELLOW}Step 3: Configuring and verifying Redis server...${NC}"

# Harden Redis configuration against Lua script execution vulnerability (CVE-2025-49844)
REDIS_CONF_FILE=""
if [ -f "/etc/redis/redis.conf" ]; then
    REDIS_CONF_FILE="/etc/redis/redis.conf"
elif [ -f "/etc/redis.conf" ]; then
    REDIS_CONF_FILE="/etc/redis.conf"
fi

if [ -n "$REDIS_CONF_FILE" ]; then
    grep -q "rename-command EVAL " "$REDIS_CONF_FILE" || echo 'rename-command EVAL ""' >> "$REDIS_CONF_FILE"
    grep -q "rename-command EVALSHA " "$REDIS_CONF_FILE" || echo 'rename-command EVALSHA ""' >> "$REDIS_CONF_FILE"
    grep -q "rename-command SCRIPT " "$REDIS_CONF_FILE" || echo 'rename-command SCRIPT ""' >> "$REDIS_CONF_FILE"
fi

systemctl enable --now redis-server 2>/dev/null || systemctl enable --now redis 2>/dev/null || true

# Test local Redis health
DEFAULT_REDIS_URL="redis://127.0.0.1:6379/0"
if redis-cli ping 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}✓ Local Redis is healthy and responding to PING (127.0.0.1:6379).${NC}"
else
    echo -e "${YELLOW}Notice: Redis service is starting on default port (127.0.0.1:6379).${NC}"
fi

# ==============================================================================
# 4. Setup Python Virtual Environment & Dependencies
# ==============================================================================
echo -e "\n${YELLOW}Step 4: Setting up Python virtual environment...${NC}"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
echo -e "${BLUE}Upgrading pip and wheel in virtual environment...${NC}"
pip install --upgrade pip setuptools wheel -q

echo -e "${BLUE}Installing python packages from requirements.txt...${NC}"
pip install -r requirements.txt -q
deactivate

echo -e "${GREEN}✓ All python libraries installed successfully.${NC}"

# ==============================================================================
# 5. Configure Environment Variables (.env)
# ==============================================================================
echo -e "\n${YELLOW}Step 5: Configuring environment variables (.env)...${NC}"

# Pre-extract existing values if .env exists
EX_API_ID=""
EX_API_HASH=""
EX_BOT_TOKEN=""
EX_ADMIN_IDS=""
EX_FILE_SIZE="20"
EX_DONATION="https://daramet.com/Hornet2002"
EX_REDIS="$DEFAULT_REDIS_URL"

if [ -f ".env" ]; then
    EX_API_ID=$(grep '^TEL_API_ID=' .env 2>/dev/null | head -n1 | cut -d'=' -f2- | tr -d '"' | tr -d "'" || true)
    EX_API_HASH=$(grep '^TEL_API_HASH=' .env 2>/dev/null | head -n1 | cut -d'=' -f2- | tr -d '"' | tr -d "'" || true)
    EX_BOT_TOKEN=$(grep '^TEL_BOT_TOKEN=' .env 2>/dev/null | head -n1 | cut -d'=' -f2- | tr -d '"' | tr -d "'" || true)
    EX_ADMIN_IDS=$(grep '^TEL_ADMIN_IDS=' .env 2>/dev/null | head -n1 | cut -d'=' -f2- | tr -d '"' | tr -d "'" || true)
    EX_FILE_SIZE=$(grep '^TEL_MAX_FILE_SIZE=' .env 2>/dev/null | head -n1 | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "20")
    EX_DONATION=$(grep '^DONATION_LINK=' .env 2>/dev/null | head -n1 | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "https://daramet.com/Hornet2002")
    EX_REDIS=$(grep '^REDIS_URL=' .env 2>/dev/null | head -n1 | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "$DEFAULT_REDIS_URL")

    echo -e "${CYAN}Existing .env configuration detected.${NC}"
    read -p "Do you want to reconfigure it? (y/N): " RECONFIG
    RECONFIG=${RECONFIG:-n}
else
    RECONFIG="y"
fi

if [[ "$RECONFIG" =~ ^[Yy]$ ]]; then
    echo -e "\n${BLUE}Please enter your bot credentials (press Enter to accept [defaults]):${NC}"

    # Prompt TEL_API_ID with validation
    while true; do
        read -p "Enter TEL_API_ID [${EX_API_ID}]: " INPUT_API_ID
        INPUT_API_ID=${INPUT_API_ID:-$EX_API_ID}
        if [[ "$INPUT_API_ID" =~ ^[0-9]+$ ]] && [ "$INPUT_API_ID" -ne 0 ]; then
            break
        fi
        echo -e "${RED}Invalid TEL_API_ID! It must be a positive integer from my.telegram.org.${NC}"
    done

    # Prompt TEL_API_HASH with validation
    while true; do
        read -p "Enter TEL_API_HASH [${EX_API_HASH}]: " INPUT_API_HASH
        INPUT_API_HASH=${INPUT_API_HASH:-$EX_API_HASH}
        if [ -n "$INPUT_API_HASH" ]; then
            break
        fi
        echo -e "${RED}TEL_API_HASH cannot be empty!${NC}"
    done

    # Prompt TEL_BOT_TOKEN with validation
    while true; do
        read -p "Enter TEL_BOT_TOKEN [${EX_BOT_TOKEN}]: " INPUT_BOT_TOKEN
        INPUT_BOT_TOKEN=${INPUT_BOT_TOKEN:-$EX_BOT_TOKEN}
        if [[ "$INPUT_BOT_TOKEN" == *":"* ]]; then
            break
        fi
        echo -e "${RED}Invalid Bot Token format! It must contain a colon (e.g. 123456:ABC-DEF).${NC}"
    done

    # Prompt TEL_ADMIN_IDS with validation
    while true; do
        read -p "Enter TEL_ADMIN_IDS (comma-separated user IDs) [${EX_ADMIN_IDS}]: " INPUT_ADMIN_IDS
        INPUT_ADMIN_IDS=${INPUT_ADMIN_IDS:-$EX_ADMIN_IDS}
        if [ -n "$INPUT_ADMIN_IDS" ]; then
            break
        fi
        echo -e "${RED}TEL_ADMIN_IDS cannot be empty! Enter your numeric Telegram user ID.${NC}"
    done

    echo ""
    read -p "Enter TEL_MAX_FILE_SIZE (MB) [Default: ${EX_FILE_SIZE:-20}]: " INPUT_MAX_FILE_SIZE
    INPUT_MAX_FILE_SIZE=${INPUT_MAX_FILE_SIZE:-${EX_FILE_SIZE:-20}}

    read -p "Enter DONATION_LINK [Default: ${EX_DONATION:-https://daramet.com/Hornet2002}]: " INPUT_DONATION
    INPUT_DONATION=${INPUT_DONATION:-${EX_DONATION:-https://daramet.com/Hornet2002}}

    echo ""
    read -p "Enter REDIS_URL [Default: ${EX_REDIS:-$DEFAULT_REDIS_URL}]: " INPUT_REDIS_URL
    INPUT_REDIS_URL=${INPUT_REDIS_URL:-${EX_REDIS:-$DEFAULT_REDIS_URL}}

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

# Optional Proxies
# TEL_PROXY_SCHEME=socks5
# TEL_PROXY_HOST=127.0.0.1
# TEL_PROXY_PORT=2080
# BALE_PROXY=
EOF
    echo -e "${GREEN}✓ .env configuration file saved.${NC}"
fi

# ==============================================================================
# 6. Setup and Start Systemd Daemon Service (Hardened Dedicated User)
# ==============================================================================
echo -e "\n${YELLOW}Step 6: Setting up hardened systemd background daemon service...${NC}"

# Create dedicated system user for bot execution if not already present
BOT_USER="tel2bale"
if ! id -u "$BOT_USER" >/dev/null 2>&1; then
    echo -e "${BLUE}Creating dedicated system user ($BOT_USER)...${NC}"
    useradd --system --no-create-home --shell /usr/sbin/nologin "$BOT_USER" 2>/dev/null || true
fi

# Ensure strict file ownership and permissions
chown -R "$BOT_USER:$BOT_USER" "$APP_DIR"
chmod 700 "$APP_DIR/cookies" 2>/dev/null || true
chmod 600 "$APP_DIR/.env" 2>/dev/null || true

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=Tel2Bale Telegram to Bale Bridge Bot Daemon
After=network.target redis-server.service

[Service]
Type=simple
User=$BOT_USER
Group=$BOT_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/python $APP_DIR/main.py
Restart=always
RestartSec=5
StartLimitIntervalSec=0
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
ReadWritePaths=$APP_DIR
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME" >/dev/null 2>&1

echo -e "${BLUE}Starting background service ($SERVICE_NAME)...${NC}"
systemctl restart "$SERVICE_NAME"

# Health Verification check
sleep 2
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "\n${GREEN}════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}  ✓ Tel2Bale bot is ONLINE and running smoothly!    ${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
else
    echo -e "\n${RED}⚠️ Warning: Service is starting or encountered an issue.${NC}"
    echo -e "${YELLOW}Recent service logs:${NC}"
    journalctl -u "$SERVICE_NAME" -n 15 --no-pager || true
fi

echo -e "\n${CYAN}${BOLD}Helpful management commands:${NC}"
echo -e "🔹 Check status:      ${YELLOW}systemctl status $SERVICE_NAME${NC}"
echo -e "🔹 View live logs:    ${YELLOW}journalctl -u $SERVICE_NAME -f${NC}"
echo -e "🔹 Restart bot:       ${YELLOW}systemctl restart $SERVICE_NAME${NC}"
echo -e "🔹 Stop bot:          ${YELLOW}systemctl stop $SERVICE_NAME${NC}"
echo -e "🔹 Configuration:     ${YELLOW}nano $APP_DIR/.env${NC}\n"
