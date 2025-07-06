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
if [ -f "$VPN_PANEL_DIR/docker-compose.yml" ]; then
  cd "$VPN_PANEL_DIR"
  docker-compose down -v || true
else
  log "No existing docker-compose.yml found, skipping container removal" "$YELLOW"
fi

log "Removing old Docker images and volumes..." "$YELLOW"
docker system prune -af || true

if [ -d "$VPN_PANEL_DIR" ]; then
  if [ -d "$VPN_PANEL_DIR/.git" ]; then
    log "Updating existing VPN Panel installation..." "$YELLOW"
    cd "$VPN_PANEL_DIR"
    git pull origin main || log "Warning: Failed to update VPN Panel repository" "$YELLOW"
  else
    log "Backing up existing non-git directory and cloning fresh..." "$YELLOW"
    mv "$VPN_PANEL_DIR" "${VPN_PANEL_DIR}_backup_$(date +%s)"
    git clone https://github.com/Kavis1/vpn-panel.git "$VPN_PANEL_DIR" || error "Failed to clone VPN Panel repository"
  fi
else
  log "Cloning VPN Panel repository..." "$YELLOW"
  git clone https://github.com/Kavis1/vpn-panel.git "$VPN_PANEL_DIR" || error "Failed to clone VPN Panel repository"
fi

cd "$VPN_PANEL_DIR"

log "Creating necessary directories..." "$YELLOW"
mkdir -p "$VPN_PANEL_DIR/logs" "$VPN_PANEL_DIR/data" "$VPN_PANEL_DIR/config" || error "Failed to create directories"

log "Validating docker-compose.yml..." "$YELLOW"
if ! python3 -c 'import yaml; yaml.safe_load(open("docker-compose.yml"))' 2>/dev/null; then
  error "Invalid docker-compose.yml file. Please check the YAML syntax."
fi

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
  if [ -f "$VPN_PANEL_DIR/.env.example" ]; then
    cp "$VPN_PANEL_DIR/.env.example" "$VPN_PANEL_DIR/.env"
  else
    log "Warning: .env.example not found, creating minimal .env file" "$YELLOW"
    cat > "$VPN_PANEL_DIR/.env" << EOF
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$(openssl rand -base64 32)
POSTGRES_DB=vpn_panel

# App
SECRET_KEY=$(openssl rand -hex 32)

# Redis
REDIS_PASSWORD=$(openssl rand -hex 32)

# Uvicorn
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000
EOF
  fi
fi

log "Building and starting VPN Panel with Docker Compose..." "$YELLOW"
cd "$VPN_PANEL_DIR"
docker-compose up -d --build || error "Failed to start VPN Panel. Please check the logs with: docker-compose logs"

success "VPN Panel started successfully!"

log "Waiting for backend to be fully up (up to 60s)..." "$YELLOW"
for i in {1..60}; do
  if curl -s http://localhost:8000/health 2>/dev/null | grep -q "ok"; then
    success "VPN Panel backend is up and running!"
    success "Access the panel at: http://$(curl -s ifconfig.me):8000"
    exit 0
  fi
  sleep 1
done

error "VPN Panel backend failed to start within 60 seconds. Check logs with: docker-compose logs backend"
