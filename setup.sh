#!/bin/bash

set -e

# Terminal Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 0. Check for root privileges
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}❌ Error: Please run this script with root (sudo) privileges${NC}"
  echo -e "${YELLOW}Example: sudo bash setup.sh${NC}"
  exit 1
fi

PROJECT_DIR=$(pwd)
SERVICE_NAME="Tel2Bale"
GITHUB_REPO="thehornet2002/tel2bale"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Telegram to Bale Bridge Bot Setup    ${NC}"
echo -e "${GREEN}========================================${NC}"

# ==========================================
# 1. Download Latest Release from GitHub
# ==========================================
echo -e "\n${YELLOW}Step 1: Downloading latest release...${NC}"

mkdir -p Tel2Bale
cd Tel2Bale

# Install necessary tools
echo -e "${BLUE}Installing required tools...${NC}"
apt-get update -qq 2>/dev/null || apt-get update
apt-get install -y -qq curl jq tar wget pkg-config git 2>/dev/null || apt-get install -y curl jq tar wget pkg-config git

echo -e "${BLUE}Fetching latest release info from GitHub...${NC}"

# Download with retry
MAX_ATTEMPTS=3
ATTEMPT=1
LATEST_TAR_URL=""

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    LATEST_TAR_URL=$(curl -s --connect-timeout 10 https://api.github.com/repos/$GITHUB_REPO/releases/latest 2>/dev/null | jq -r '.tarball_url' 2>/dev/null || echo "null")
    
    if [ "$LATEST_TAR_URL" != "null" ] && [ -n "$LATEST_TAR_URL" ]; then
        break
    fi
    
    echo -e "${YELLOW}Attempt $ATTEMPT failed, retrying...${NC}"
    ATTEMPT=$((ATTEMPT + 1))
    sleep 2
done

if [ "$LATEST_TAR_URL" == "null" ] || [ -z "$LATEST_TAR_URL" ]; then
    echo -e "${RED}❌ Error: Could not fetch the latest release${NC}"
    echo -e "${YELLOW}Make sure:${NC}"
    echo -e "${YELLOW}  - Repository is PUBLIC${NC}"
    echo -e "${YELLOW}  - A Release is published${NC}"
    echo -e "${YELLOW}  - Internet connection is active${NC}"
    exit 1
fi

echo -e "${BLUE}Downloading source code...${NC}"
if ! wget -q --timeout=30 -O release.tar.gz "$LATEST_TAR_URL"; then
    echo -e "${RED}❌ Error: Download failed${NC}"
    exit 1
fi

echo -e "${BLUE}Extracting files...${NC}"
tar -xzf release.tar.gz --strip-components=1 2>/dev/null
rm -f release.tar.gz

echo -e "${GREEN}✓ Latest release successfully downloaded and extracted${NC}"

# ==========================================
# 2. Install Python 3.12 or 3.11
# ==========================================
echo -e "\n${YELLOW}Step 2: Installing Python...${NC}"

apt-get update -qq 2>/dev/null || true

# First check which version is available
PYTHON_VERSION=""
if command -v python3.12 &>/dev/null; then
    PYTHON_VERSION="3.12"
    echo -e "${GREEN}✓ Python 3.12 already installed${NC}"
elif command -v python3.11 &>/dev/null; then
    PYTHON_VERSION="3.11"
    echo -e "${GREEN}✓ Python 3.11 already installed${NC}"
elif command -v python3.10 &>/dev/null; then
    PYTHON_VERSION="3.10"
    echo -e "${GREEN}✓ Python 3.10 already installed${NC}"
else
    echo -e "${BLUE}Python not found, installing...${NC}"
    
    apt-get install -y software-properties-common 2>/dev/null || true
    
    # Try to install Python 3.12
    if apt-cache search python3.12 2>/dev/null | grep -q python3.12; then
        apt-get install -y python3.12 python3.12-venv python3-pip 2>/dev/null
        PYTHON_VERSION="3.12"
    # If Python 3.12 not available, try 3.11
    elif apt-cache search python3.11 2>/dev/null | grep -q python3.11; then
        apt-get install -y python3.11 python3.11-venv python3-pip 2>/dev/null
        PYTHON_VERSION="3.11"
    else
        # Last resort - default Python 3
        apt-get install -y python3 python3-venv python3-pip 2>/dev/null
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    fi
fi

if [ -z "$PYTHON_VERSION" ]; then
    echo -e "${RED}❌ Error: Python installation failed${NC}"
    exit 1
fi

PYTHON_EXEC="python$PYTHON_VERSION"

if ! command -v $PYTHON_EXEC &>/dev/null; then
    PYTHON_EXEC="python3"
fi

echo -e "${GREEN}✓ Using: $($PYTHON_EXEC --version)${NC}"

# Install venv package for the specific Python version
echo -e "${BLUE}Installing venv package for Python $PYTHON_VERSION...${NC}"
if [ "$PYTHON_VERSION" != "3" ]; then
    apt-get install -y python${PYTHON_VERSION}-venv 2>/dev/null || {
        echo -e "${YELLOW}Falling back to python3-venv...${NC}"
        apt-get install -y python3-venv 2>/dev/null
    }
else
    apt-get install -y python3-venv 2>/dev/null
fi

# ==========================================
# 3. Virtual Environment Setup
# ==========================================
echo -e "\n${YELLOW}Step 3: Creating virtual environment...${NC}"

cd "$PROJECT_DIR/Tel2Bale"

if [ ! -d "venv" ]; then
    if $PYTHON_EXEC -m venv venv 2>/dev/null; then
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    else
        echo -e "${RED}❌ Error: Failed to create virtual environment${NC}"
        echo -e "${YELLOW}Trying with --without-pip option...${NC}"
        $PYTHON_EXEC -m venv venv --without-pip
        echo -e "${GREEN}✓ Virtual environment created (without pip)${NC}"
    fi
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# ==========================================
# 4. Install Build Tools and Development Headers
# ==========================================
echo -e "\n${YELLOW}Step 4: Installing build tools...${NC}"

echo -e "${BLUE}Installing build-essential and Python development headers...${NC}"
apt-get install -y build-essential 2>/dev/null || {
    echo -e "${YELLOW}Retrying apt-get update...${NC}"
    apt-get update && apt-get install -y build-essential
}

if [ "$PYTHON_VERSION" != "3" ]; then
    apt-get install -y python${PYTHON_VERSION}-dev 2>/dev/null || apt-get install -y python3-dev
else
    apt-get install -y python3-dev 2>/dev/null
fi

echo -e "${GREEN}✓ Build tools installed${NC}"

# ==========================================
# 5. Install Python Dependencies
# ==========================================
echo -e "\n${YELLOW}Step 5: Installing Python dependencies...${NC}"

if [ -f "requirements.txt" ]; then
    source venv/bin/activate
    
    echo -e "${BLUE}Upgrading pip, setuptools, and wheel...${NC}"
    pip install --upgrade pip setuptools wheel 2>&1 | grep -v "already satisfied" || true
    
    echo -e "${BLUE}Installing requirements.txt (this may take a while)...${NC}"
    if pip install -r requirements.txt 2>&1 | tee /tmp/pip_install.log; then
        echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
    else
        echo -e "${RED}❌ Error during dependency installation${NC}"
        echo -e "${YELLOW}Last 20 lines of error:${NC}"
        tail -20 /tmp/pip_install.log
        deactivate
        exit 1
    fi
    
    deactivate
else
    echo -e "${RED}❌ Error: requirements.txt not found!${NC}"
    exit 1
fi

# ==========================================
# 6. Generate .env Configuration File
# ==========================================
echo -e "\n${YELLOW}Step 6: Configuration setup (.env)${NC}"

read -p "Enter TEL_API_ID: " INPUT_API_ID
read -p "Enter TEL_API_HASH: " INPUT_API_HASH
read -p "Enter TEL_BOT_TOKEN: " INPUT_BOT_TOKEN
read -p "Enter TEL_ADMIN_IDS (comma-separated): " INPUT_ADMIN_IDS

echo ""
echo -e "${YELLOW}--- Maximum File Size Configuration ---${NC}"
read -p "Enter TEL_MAX_FILE_SIZE [Default: 20]: " INPUT_MAX_FILE_SIZE
INPUT_MAX_FILE_SIZE=${INPUT_MAX_FILE_SIZE:-20}

if ! [[ "$INPUT_MAX_FILE_SIZE" =~ ^[0-9]+$ ]]; then
    echo -e "${RED}Invalid numeric input. Using default (20)${NC}"
    INPUT_MAX_FILE_SIZE=20
fi

echo ""
echo -e "${RED}⚠ WARNING: IN_MEMORY CONFIGURATION${NC}"
echo -e "${YELLOW}Setting TEL_IN_MEMORY to True means files will be held entirely in RAM.${NC}"

read -p "Do you want to enable TEL_IN_MEMORY? (True/False) [Default: False]: " INPUT_IN_MEMORY
INPUT_IN_MEMORY=${INPUT_IN_MEMORY:-False}

if [[ "$INPUT_IN_MEMORY" != "True" && "$INPUT_IN_MEMORY" != "False" ]]; then
    echo -e "${RED}Invalid input. Using default (False)${NC}"
    INPUT_IN_MEMORY="False"
fi

EXTRACTED_START="Welcome to the bot!"
EXTRACTED_HELP="Here is the help guide."

if [ -f "example.env" ]; then
    TEMP_START=$(grep '^TEL_START_TXT=' example.env 2>/dev/null | sed 's/^TEL_START_TXT=//' | tr -d '"' | tr -d "'" || echo "")
    TEMP_HELP=$(grep '^TEL_HELP_TXT=' example.env 2>/dev/null | sed 's/^TEL_HELP_TXT=//' | tr -d '"' | tr -d "'" || echo "")

    [ -n "$TEMP_START" ] && EXTRACTED_START="$TEMP_START"
    [ -n "$TEMP_HELP" ] && EXTRACTED_HELP="$TEMP_HELP"
fi

cat <<EOF > .env
TEL_API_ID=$INPUT_API_ID
TEL_API_HASH=$INPUT_API_HASH
TEL_BOT_TOKEN=$INPUT_BOT_TOKEN
TEL_ADMIN_IDS=$INPUT_ADMIN_IDS

TEL_START_TXT="$EXTRACTED_START"
TEL_HELP_TXT="$EXTRACTED_HELP"

TEL_ADS_CHANNELS=

TEL_MAX_FILE_SIZE=$INPUT_MAX_FILE_SIZE
TEL_IN_MEMORY=$INPUT_IN_MEMORY

TEL_PROXY_SCHEME=
TEL_PROXY_HOST=
TEL_PROXY_PORT=
EOF

echo -e "${GREEN}✓ .env file created successfully${NC}"

# ==========================================
# 7. Create and Start Systemd Service
# ==========================================
echo -e "\n${YELLOW}Step 7: Creating systemd service...${NC}"

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=Telegram to Bale Bridge Bot Daemon
After=network.target

[Service]
User=root
WorkingDirectory=$PROJECT_DIR/Tel2Bale
ExecStart=$PROJECT_DIR/Tel2Bale/venv/bin/python $PROJECT_DIR/Tel2Bale/main.py
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

echo -e "${BLUE}Starting service...${NC}"
if systemctl restart "$SERVICE_NAME" 2>/dev/null; then
    echo -e "${GREEN}✓ Service started successfully${NC}"
else
    echo -e "${RED}⚠ Error starting service${NC}"
    echo -e "${YELLOW}Use this command to see details:${NC}"
    echo -e "${BLUE}journalctl -u $SERVICE_NAME -n 20${NC}"
fi

echo -e "\n${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Installation completed successfully!  ${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"

echo -e "\n${BLUE}Useful commands:${NC}"
echo -e "🔹 Bot status:      ${YELLOW}sudo systemctl status $SERVICE_NAME${NC}"
echo -e "🔹 View live logs:  ${YELLOW}sudo journalctl -u $SERVICE_NAME -f${NC}"
echo -e "🔹 Last 20 lines:   ${YELLOW}sudo journalctl -u $SERVICE_NAME -n 20${NC}"
echo -e "🔹 Stop bot:        ${YELLOW}sudo systemctl stop $SERVICE_NAME${NC}"
echo -e "🔹 Restart bot:     ${YELLOW}sudo systemctl restart $SERVICE_NAME${NC}"

echo -e "\n${YELLOW}Note: To change settings later, edit the .env file and restart the bot${NC}"
