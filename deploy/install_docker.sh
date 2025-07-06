#!/bin/bash

# Exit on any error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log messages
function log() {
  echo -e "${2}[*] $1 ${NC}"
}

function error() {
  echo -e "${RED}[-] $1 ${NC}"
  exit 1
}

function success() {
  echo -e "${GREEN}[+] $1 ${NC}"
}

# Check if script is run with sudo
if [ "$EUID" -ne 0 ]; then 
  error "This script must be run as root (use sudo)"
fi

# VPN Panel installation directory
VPN_PANEL_DIR="/root/vpn-panel"

log "Stopping and removing existing containers..." "$YELLOW"
docker-compose down -v || true

log "Removing old Docker images and volumes..." "$YELLOW"
docker system prune -af || true

if [ -d "$VPN_PANEL_DIR" ]; then
  log "Updating existing VPN Panel installation..." "$YELLOW"
  cd "$VPN_PANEL_DIR"
  git pull origin main || error "Failed to update VPN Panel repository"
else
  log "Cloning VPN Panel repository..." "$YELLOW"
  git clone https://github.com/Kavis1/vpn-panel.git "$VPN_PANEL_DIR" || error "Failed to clone VPN Panel repository"
  cd "$VPN_PANEL_DIR"
fi

log "Creating necessary directories..." "$YELLOW"
mkdir -p "$VPN_PANEL_DIR/logs" "$VPN_PANEL_DIR/data" "$VPN_PANEL_DIR/config" || error "Failed to create directories"

log "Creating Xray configuration..." "$YELLOW"
if [ ! -f "$VPN_PANEL_DIR/config/xray.json" ]; then
  cat > "$VPN_PANEL_DIR/config/xray.json" << EOF
{
  "log": {
    "access": "/var/log/xray/access.log",
    "error": "/var/log/xray/error.log",
    "loglevel": "warning"
  },
  "inbounds": [],
  "outbounds": [
    {
      "protocol": "freedom",
      "settings": {}
    }
  ]
}
EOF
fi

log "Creating .env file if not exists..." "$YELLOW"
if [ ! -f "$VPN_PANEL_DIR/.env" ]; then
  cp "$VPN_PANEL_DIR/.env.example" "$VPN_PANEL_DIR/.env" || error "Failed to create .env file"
fi

log "Starting VPN Panel with Docker Compose..." "$YELLOW"
docker-compose up -d --build || error "Failed to start VPN Panel. Please check the logs with: docker-compose logs"

success "VPN Panel started successfully!"

log "Waiting for backend to be fully up (up to 60s)..." "$YELLOW"
for i in {1..60}; do
  if curl -s http://localhost:8000/health | grep -q "ok"; then
    success "VPN Panel backend is up and running!"
    exit 0
  fi
  sleep 1
done

error "VPN Panel backend failed to start within 60 seconds. Check logs with: docker-compose logs backend"
