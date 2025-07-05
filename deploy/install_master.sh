#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${YELLOW}[*] $1${NC}"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}[+] $1${NC}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}[-] $1${NC}"
    exit 1
}

# Check if script is run as root
if [ "$(id -u)" -ne 0 ]; then
    print_error "This script must be run as root"
fi

# Get user input
read -p "Enter your domain name (or press Enter to use IP address): " DOMAIN
read -p "Enter admin email (for Let's Encrypt): " EMAIL
read -p "Enter admin username: " ADMIN_USER
read -s -p "Enter admin password: " ADMIN_PASS
echo ""

# Set default values if not provided
[ -z "$DOMAIN" ] && DOMAIN=$(hostname -I | awk '{print $1}')
[ -z "$EMAIL" ] && EMAIL="admin@$DOMAIN"
[ -z "$ADMIN_USER" ] && ADMIN_USER="admin"
[ -z "$ADMIN_PASS" ] && ADMIN_PASS=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 16)

print_status "Starting VPN Panel Master Server installation..."

# Check if directory exists and handle it
if [ -d "/opt/vpn-panel/backend" ]; then
    print_status "Directory /opt/vpn-panel/backend already exists."
    read -p "Do you want to remove it and start fresh? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Removing existing directory..."
        rm -rf /opt/vpn-panel/backend || print_error "Failed to remove existing directory"
    else
        print_status "Updating existing installation..."
        cd /opt/vpn-panel/backend
        git fetch origin
        git reset --hard origin/main
        git clean -fd
    fi
fi

# Create directory if it doesn't exist
mkdir -p /opt/vpn-panel/backend

# Update system
print_status "Updating system packages..."
apt-get update && apt-get upgrade -y || print_error "Failed to update system packages"

# Install required packages
print_status "Installing required packages..."
apt-get install -y git curl wget python3-pip python3-venv nginx postgresql postgresql-contrib certbot python3-certbot-nginx || print_error "Failed to install required packages"

# Install Docker and Docker Compose
print_status "Installing Docker and Docker Compose..."
curl -fsSL https://get.docker.com -o get-docker.sh || print_error "Failed to download Docker installation script"
sh get-docker.sh || print_error "Failed to install Docker"
usermod -aG docker $USER || print_error "Failed to add user to docker group"
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose || print_error "Failed to download Docker Compose"
chmod +x /usr/local/bin/docker-compose || print_error "Failed to make Docker Compose executable"

# Create project directory
print_status "Setting up project directory..."
mkdir -p /opt/vpn-panel/{backend,frontend,data/{postgres,redis,certs}} || print_error "Failed to create project directories"

# Clone repository
print_status "Cloning VPN Panel repository..."
git clone https://github.com/Kavis1/vpn-panel.git /opt/vpn-panel/backend || print_error "Failed to clone repository"

# Set up Python virtual environment
print_status "Setting up Python virtual environment..."
python3 -m venv /opt/vpn-panel/backend/venv || print_error "Failed to create Python virtual environment"
source /opt/vpn-panel/backend/venv/bin/activate || print_error "Failed to activate virtual environment"
pip install --upgrade pip || print_error "Failed to upgrade pip"

# Install Python dependencies
print_status "Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt || print_error "Failed to install Python dependencies"

# Install additional required packages for database
print_status "Installing database dependencies..."
pip install alembic psycopg2-binary || print_error "Failed to install database dependencies"

# Configure alembic.ini
print_status "Configuring database migrations..."
if [ -f "/opt/vpn-panel/backend/alembic.ini" ]; then
    print_status "alembic.ini already exists, skipping..."
else
    cp /opt/vpn-panel/backend/alembic.ini.example /opt/vpn-panel/backend/alembic.ini || print_error "Failed to copy alembic.ini"
    sed -i "s/\$POSTGRES_USER/$POSTGRES_USER/g" /opt/vpn-panel/backend/alembic.ini
    sed -i "s/\$POSTGRES_PASSWORD/$POSTGRES_PASSWORD/g" /opt/vpn-panel/backend/alembic.ini
    sed -i "s/\$POSTGRES_HOST/$POSTGRES_HOST/g" /opt/vpn-panel/backend/alembic.ini
    sed -i "s/\$POSTGRES_PORT/$POSTGRES_PORT/g" /opt/vpn-panel/backend/alembic.ini
    sed -i "s/\$POSTGRES_DB/$POSTGRES_DB/g" /opt/vpn-panel/backend/alembic.ini
fi

# Configure environment variables
print_status "Configuring environment variables..."
cat > /opt/vpn-panel/backend/.env <<EOL
# Application
APP_ENV=production
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)

# Database
DATABASE_URL=postgresql://vpnpanel:$(openssl rand -hex 16)@localhost:5432/vpnpanel

# JWT
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# First Superuser
FIRST_SUPERUSER_EMAIL=${EMAIL}
FIRST_SUPERUSER_PASSWORD=${ADMIN_PASS}
FIRST_SUPERUSER_USERNAME=${ADMIN_USER}

# Xray
XRAY_EXECUTABLE_PATH=/usr/local/bin/xray
XRAY_CONFIG_DIR=/etc/xray
XRAY_API_ADDRESS=localhost
XRAY_API_PORT=8080
XRAY_API_TAG=api

# HWID Device Limits
HWID_DEVICE_LIMIT_ENABLED=True
HWID_FALLBACK_DEVICE_LIMIT=5

# Server
SERVER_NAME=${DOMAIN}
SERVER_HOST=https://${DOMAIN}
FRONTEND_URL=https://${DOMAIN}
EOL

# Set up PostgreSQL
print_status "Configuring PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE vpnpanel;" || print_error "Failed to create database"
sudo -u postgres psql -c "CREATE USER vpnpanel WITH PASSWORD '$(grep -oP 'DATABASE_URL=.*?@' /opt/vpn-panel/backend/.env | cut -d':' -f3 | cut -d'@' -f1)';" || print_error "Failed to create database user"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE vpnpanel TO vpnpanel;" || print_error "Failed to grant database privileges"

# Run database migrations
print_status "Running database migrations..."
cd /opt/vpn-panel/backend

# Initialize alembic if not already initialized
if [ ! -d "/opt/vpn-panel/backend/alembic" ]; then
    print_status "Initializing alembic..."
    alembic init alembic || print_error "Failed to initialize alembic"
    
    # Copy our custom env.py
    cp /opt/vpn-panel/backend/alembic.ini.example /opt/vpn-panel/backend/alembic.ini
    cp /opt/vpn-panel/backend/alembic/env.py /opt/vpn-panel/backend/alembic/env.py
    cp /opt/vpn-panel/backend/alembic/script.py.mako /opt/vpn-panel/backend/alembic/script.py.mako
    
    # Create versions directory
    mkdir -p /opt/vpn-panel/backend/alembic/versions
    touch /opt/vpn-panel/backend/alembic/versions/.gitkeep
    
    # Create initial migration
    print_status "Creating initial migration..."
    alembic revision --autogenerate -m "Initial migration" || print_error "Failed to create initial migration"
fi

# Run migrations
alembic upgrade head || print_error "Failed to run database migrations"

# Install Xray
print_status "Installing Xray..."
wget -O /tmp/xray.zip https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip || print_error "Failed to download Xray"
unzip /tmp/xray.zip -d /tmp/xray || print_error "Failed to extract Xray"
install -m 755 /tmp/xray/xray /usr/local/bin/ || print_error "Failed to install Xray"
rm -rf /tmp/xray /tmp/xray.zip

# Configure Xray
mkdir -p /etc/xray
cat > /etc/xray/config.json << 'EOL'
{
  "log": {
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "port": 443,
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "$(cat /proc/sys/kernel/random/uuid)",
            "flow": "xtls-rprx-direct"
          }
        ],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "tcp",
        "security": "tls",
        "tlsSettings": {
          "certificates": [
            {
              "certificateFile": "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem",
              "keyFile": "/etc/letsencrypt/live/${DOMAIN}/privkey.pem"
            }
          ]
        }
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom"
    }
  ],
  "routing": {
    "domainStrategy": "AsIs",
    "rules": [
      {
        "type": "field",
        "ip": [
          "geoip:private"
        ],
        "outboundTag": "blocked"
      },
      {
        "type": "field",
        "domain": [
          "geosite:category-ads-all"
        ],
        "outboundTag": "blocked"
      }
    ]
  },
  "policy": {
    "levels": {
      "0": {
        "handshake": 4,
        "connIdle": 300,
        "uplinkOnly": 1,
        "downlinkOnly": 1
      }
    }
  }
}
EOL

# Set up SSL certificates
if [ "$DOMAIN" != "$(hostname -I | awk '{print $1}')" ]; then
    print_status "Setting up SSL certificates with Let's Encrypt..."
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect || print_error "Failed to set up SSL certificates"
    
    # Set up certificate renewal
    (crontab -l 2>/dev/null; echo "0 0 * * * certbot renew --quiet --deploy-hook 'systemctl reload nginx'") | crontab - || print_error "Failed to set up certificate renewal"
else
    print_status "Using self-signed certificate (no domain specified)..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/ssl/private/nginx-selfsigned.key \
        -out /etc/ssl/certs/nginx-selfsigned.crt \
        -subj "/CN=$DOMAIN" || print_error "Failed to generate self-signed certificate"
fi

# Configure Nginx
print_status "Configuring Nginx..."
cat > /etc/nginx/sites-available/vpn-panel << EOL
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /static/ {
        alias /opt/vpn-panel/backend/app/static/;
        expires 30d;
        access_log off;
    }
}
EOL

ln -sf /etc/nginx/sites-available/vpn-panel /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Create systemd service for backend
print_status "Creating systemd service for backend..."
cat > /etc/systemd/system/vpn-panel.service << EOL
[Unit]
Description=VPN Panel Backend
After=network.target postgresql.service

[Service]
User=root
WorkingDirectory=/opt/vpn-panel/backend
Environment="PATH=/opt/vpn-panel/backend/venv/bin"
ExecStart=/opt/vpn-panel/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Create systemd service for Xray
cat > /etc/systemd/system/xray.service << EOL
[Unit]
Description=Xray Service
After=network.target nss-lookup.target

[Service]
User=nobody
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
NoNewPrivileges=true
ExecStart=/usr/local/bin/xray run -config /etc/xray/config.json
Restart=on-failure
RestartPreventExitStatus=23
LimitNPROC=10000
LimitNOFILE=1000000

[Install]
WantedBy=multi-user.target
EOL

# Enable and start services
print_status "Starting services..."
systemctl daemon-reload
systemctl enable vpn-panel xray nginx postgresql
systemctl restart vpn-panel xray nginx postgresql || print_error "Failed to start services"

# Create admin user
print_status "Creating admin user..."
cd /opt/vpn-panel/backend && python -c "
import asyncio
from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.user import User

async def create_admin():
    async with AsyncSessionLocal() as session:
        user = await session.get(User, 1)
        if not user:
            user = User(
                email='$EMAIL',
                username='$ADMIN_USER',
                hashed_password=get_password_hash('$ADMIN_PASS'),
                is_active=True,
                is_superuser=True,
                is_verified=True
            )
            session.add(user)
            await session.commit()

asyncio.run(create_admin())
" || print_error "Failed to create admin user"

# Print installation summary
print_success "\n=================================================="
print_success "  VPN Panel Master Server Installation Complete"
print_success "=================================================="
echo -e "\n${GREEN}Access your VPN Panel:${NC} https://$DOMAIN"
echo -e "${GREEN}Admin Username:${NC} $ADMIN_USER"
echo -e "${GREEN}Admin Password:${NC} $ADMIN_PASS"
echo -e "\n${YELLOW}Please change the default admin password after first login.${NC}"

print_success "\nInstallation completed successfully!"
