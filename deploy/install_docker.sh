#!/bin/bash

# Exit on any error
set -e

# Enable verbose output for debugging
set -x

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="/var/log/vpn_panel_install.log"

# Function to log messages
function log() {
  local timestamp
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo -e "${2}[*] $1 ${NC}"
  echo -e "[${timestamp}] [INFO] $1" >> "$LOG_FILE"
}

function error() {
  local timestamp
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo -e "${RED}[-] $1 ${NC}" >&2
  echo -e "[${timestamp}] [ERROR] $1" >> "$LOG_FILE"
  exit 1
}

function success() {
  local timestamp
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo -e "${GREEN}[+] $1 ${NC}"
  echo -e "[${timestamp}] [SUCCESS] $1" >> "$LOG_FILE"
}

function debug() {
  if [ "${DEBUG:-0}" -eq 1 ]; then
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}[DEBUG] $1 ${NC}"
    echo -e "[${timestamp}] [DEBUG] $1" >> "$LOG_FILE"
  fi
}

# Check if script is run with sudo
if [ "$EUID" -ne 0 ]; then 
  error "This script must be run as root (use sudo)"
fi

# VPN Panel installation directory
VPN_PANEL_DIR="/root/vpn-panel"
FRONTEND_DIR="$VPN_PANEL_DIR/frontend"

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

echo "VPN Panel installation started at $(date)" > "$LOG_FILE"

# Check for required commands
for cmd in docker docker-compose curl git node npm npx; do
  if ! command -v "$cmd" &> /dev/null; then
    log "Command $cmd is required but not installed. Installing..." "$YELLOW"
    
    if [ -f /etc/debian_version ]; then
      # Debian/Ubuntu
      apt-get update
      if [ "$cmd" = "docker" ]; then
        apt-get install -y docker.io
      elif [ "$cmd" = "docker-compose" ]; then
        apt-get install -y docker-compose
      else
        apt-get install -y "$cmd"
      fi
    elif [ -f /etc/redhat-release ]; then
      # RHEL/CentOS
      if [ "$cmd" = "docker" ]; then
        yum install -y docker
        systemctl enable --now docker
      elif [ "$cmd" = "docker-compose" ]; then
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
      else
        yum install -y "$cmd"
      fi
    else
      error "Unsupported OS. Please install $cmd manually."
    fi
  fi
done

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
log "Creating necessary directories..." "$YELLOW"
mkdir -p "$VPN_PANEL_DIR/logs" "$VPN_PANEL_DIR/data" "$VPN_PANEL_DIR/config" "$FRONTEND_DIR" || error "Failed to create directories"

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

# Install Node.js if not installed
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
  log "Installing Node.js and npm..." "$YELLOW"
  
  if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
  elif [ -f /etc/redhat-release ]; then
    # RHEL/CentOS
    curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
    yum install -y nodejs
  else
    error "Unsupported OS. Please install Node.js manually."
  fi
  
  # Verify installation
  if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    error "Failed to install Node.js and npm. Please install them manually."
  fi
  
  success "Node.js and npm installed successfully!"
fi

# Install frontend dependencies if frontend directory exists
if [ -d "$FRONTEND_DIR" ]; then
  log "Setting up frontend..." "$YELLOW"
  
  cd "$FRONTEND_DIR"
  
  # Install npm dependencies
  log "Installing frontend dependencies..." "$YELLOW"
  npm install --legacy-peer-deps >> "$LOG_FILE" 2>&1 || error "Failed to install frontend dependencies. Check $LOG_FILE for details."
  
  # Build frontend
  log "Building frontend..." "$YELLOW"
  npm run build >> "$LOG_FILE" 2>&1 || error "Failed to build frontend. Check $LOG_FILE for details."
  
  success "Frontend built successfully!"
  
  cd "$VPN_PANEL_DIR"
else
  log "Frontend directory not found at $FRONTEND_DIR, skipping frontend setup" "$YELLOW"
fi

# Build and start Docker containers
log "Building and starting VPN Panel with Docker Compose..." "$YELLOW"
cd "$VPN_PANEL_DIR"

docker-compose up -d --build >> "$LOG_FILE" 2>&1 || {
  error "Failed to start VPN Panel. Check $LOG_FILE and run 'docker-compose logs' for details."
}

success "VPN Panel started successfully!"

# Function to check service health
check_service_health() {
  local service_name=$1
  local port=$2
  local max_retries=30
  local retry_interval=5
  
  log "Waiting for $service_name to be fully up (up to $((max_retries * retry_interval))s)..." "$YELLOW"
  
  for ((i=1; i<=max_retries; i++)); do
    # Check if container is running
    if ! docker ps | grep -q "vpn-panel-${service_name}"; then
      error "$service_name container is not running. Check logs with: docker-compose logs $service_name"
    fi
    
    # Check health status
    if curl -s -f "http://localhost:${port}/health" 2>/dev/null | grep -q "ok"; then
      success "$service_name is up and running!"
      return 0
    fi
    
    # Show progress
    if (( i % 5 == 0 )); then
      log "Still waiting for $service_name to start... (${i}/${max_retries})" "$YELLOW"
      docker-compose logs --tail=20 "$service_name"
    fi
    
    sleep "$retry_interval"
  done
  
  error "$service_name failed to start within $((max_retries * retry_interval)) seconds. Check logs with: docker-compose logs --tail=100 $service_name"
}

# Check backend health
check_service_health "backend" "8000"

# If frontend is running, check its health
if docker ps | grep -q "vpn-panel-frontend"; then
  check_service_health "frontend" "3000"
  success "Access the panel at: http://$(curl -s ifconfig.me):3000"
else
  success "Access the API at: http://$(curl -s ifconfig.me):8000"
  log "Frontend is not running. To start it, run: cd $FRONTEND_DIR && npm start" "$YELLOW"
fi

# Show final instructions
log "Installation completed at $(date)" "$GREEN"
log "Full installation log is available at: $LOG_FILE" "$GREEN"
log "To view logs, run: docker-compose logs -f" "$YELLOW"
log "To stop the services, run: cd $VPN_PANEL_DIR && docker-compose down" "$YELLOW"
log "To update the panel, simply run this script again" "$YELLOW"
