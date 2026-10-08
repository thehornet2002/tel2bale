#!/bin/bash

set -e

# Terminal Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}   🚀 TEL2BALE — Automated Docker Setup & Deploy   ${NC}"
echo -e "${GREEN}====================================================${NC}"

# 0. Check root privileges
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}❌ Error: This script must be run as root (or with sudo).${NC}"
  echo -e "${YELLOW}Usage: sudo bash setup_docker.sh${NC}"
  exit 1
fi

GITHUB_REPO="thehornet2002/tel2bale"
TARGET_DIR="tel2bale"

# 1. Install prerequisites (curl, git, jq)
echo -e "\n${YELLOW}Step 1: Checking and installing essential system tools...${NC}"
if command -v apt-get &>/dev/null; then
    apt-get update -qq 2>/dev/null || apt-get update
    apt-get install -y -qq curl git jq ca-certificates gnupg 2>/dev/null || apt-get install -y curl git jq ca-certificates gnupg
elif command -v yum &>/dev/null; then
    yum install -y curl git jq ca-certificates gnupg
elif command -v dnf &>/dev/null; then
    dnf install -y curl git jq ca-certificates gnupg
elif command -v pacman &>/dev/null; then
    pacman -Sy --noconfirm curl git jq ca-certificates
fi
echo -e "${GREEN}✓ Essential tools ready.${NC}"

# 2. Check and Install Docker & Docker Compose
echo -e "\n${YELLOW}Step 2: Checking and installing Docker & Docker Compose...${NC}"
if ! command -v docker &>/dev/null; then
    echo -e "${BLUE}Docker not found. Installing Docker Engine automatically...${NC}"
    curl -fsSL https://get.docker.com | sh
    systemctl enable --now docker 2>/dev/null || true
    echo -e "${GREEN}✓ Docker Engine successfully installed and started.${NC}"
else
    echo -e "${GREEN}✓ Docker already installed: $(docker --version)${NC}"
    systemctl start docker 2>/dev/null || true
fi

# Configure Docker daemon DNS to avoid container build DNS failures
mkdir -p /etc/docker
if [ ! -f /etc/docker/daemon.json ]; then
    echo '{"dns": ["8.8.8.8", "1.1.1.1"]}' > /etc/docker/daemon.json
    systemctl restart docker 2>/dev/null || true
elif ! grep -q '"dns"' /etc/docker/daemon.json; then
    tmp=$(mktemp)
    if jq '. + {"dns": ["8.8.8.8", "1.1.1.1"]}' /etc/docker/daemon.json > "$tmp" 2>/dev/null; then
        mv "$tmp" /etc/docker/daemon.json
        systemctl restart docker 2>/dev/null || true
    else
        rm -f "$tmp"
    fi
fi

# Verify Docker Compose (v2 plugin or binary)
DOCKER_COMPOSE_CMD=""
if docker compose version &>/dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo -e "${BLUE}Docker Compose plugin not found. Installing...${NC}"
    if command -v apt-get &>/dev/null; then
        apt-get install -y -qq docker-compose-plugin 2>/dev/null || true
    elif command -v yum &>/dev/null; then
        yum install -y docker-compose-plugin 2>/dev/null || true
    fi

    if docker compose version &>/dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | jq -r .tag_name || echo "v2.24.5")
        curl -SL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        DOCKER_COMPOSE_CMD="docker-compose"
    fi
fi
echo -e "${GREEN}✓ Docker Compose ready ($($DOCKER_COMPOSE_CMD version | head -n1))${NC}"

# 3. Clone or pull repository
echo -e "\n${YELLOW}Step 3: Fetching latest source code...${NC}"
if [ -f "Dockerfile" ] && [ -f "docker-compose.yml" ]; then
    echo -e "${GREEN}✓ Already inside project directory.${NC}"
    git pull origin main 2>/dev/null || true
else
    if [ -d "$TARGET_DIR" ]; then
        cd "$TARGET_DIR"
        git pull origin main 2>/dev/null || true
    else
        git clone "https://github.com/${GITHUB_REPO}.git" "$TARGET_DIR"
        cd "$TARGET_DIR"
    fi
fi

# Prepare directories and database file for persistent volumes
mkdir -p logs backups downloads redis_data
touch bot.db

# 4. Configure .env file
echo -e "\n${YELLOW}Step 4: Configuring environment variables (.env)...${NC}"
if [ -f ".env" ]; then
    echo -e "${CYAN}.env file already exists.${NC}"
    read -p "Do you want to reconfigure it? (y/N): " RECONFIG
    RECONFIG=${RECONFIG:-n}
else
    RECONFIG="y"
fi

if [[ "$RECONFIG" =~ ^[Yy]$ ]]; then
    echo -e "\n${BLUE}Please enter your configuration values:${NC}"

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
    echo -e "${CYAN}Note: Redis is mandatory. A dedicated Redis container is automatically deployed.${NC}"
    read -p "Enter REDIS_URL [Default: redis://redis:6379/0]: " INPUT_REDIS_URL
    INPUT_REDIS_URL=${INPUT_REDIS_URL:-redis://redis:6379/0}

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
else
    # Ensure REDIS_URL exists in existing .env
    if ! grep -q "^REDIS_URL=" .env; then
        echo "REDIS_URL=redis://redis:6379/0" >> .env
    fi
fi

# 5. Build & Launch Docker Containers
echo -e "\n${YELLOW}Step 5: Building images and starting containers...${NC}"
$DOCKER_COMPOSE_CMD down 2>/dev/null || true
$DOCKER_COMPOSE_CMD up -d --build

echo -e "\n${GREEN}════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Deployment completed successfully!             ${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"

echo -e "\n${CYAN}Helpful management commands:${NC}"
echo -e "🔹 View live logs:     ${YELLOW}$DOCKER_COMPOSE_CMD logs -f${NC}"
echo -e "🔹 Container status:   ${YELLOW}$DOCKER_COMPOSE_CMD ps${NC}"
echo -e "🔹 Restart bot:        ${YELLOW}$DOCKER_COMPOSE_CMD restart${NC}"
echo -e "🔹 Stop bot:           ${YELLOW}$DOCKER_COMPOSE_CMD down${NC}"
echo -e "🔹 Rebuild & update:   ${YELLOW}$DOCKER_COMPOSE_CMD up -d --build${NC}"
