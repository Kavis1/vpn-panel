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

# Clone or update repository
print_status "Setting up VPN Panel repository..."
mkdir -p /opt/vpn-panel

if [ -d "/opt/vpn-panel/backend" ]; then
    cd /opt/vpn-panel/backend
    
    if [ -d ".git" ]; then
        # If it's a git repository, update it
        print_status "Updating existing repository..."
        git fetch origin
        git reset --hard origin/main
        git clean -fd
    else
        # If directory exists but is not a git repository
        print_status "Directory exists but is not a git repository. Initializing..."
        git init
        git remote add origin https://github.com/Kavis1/vpn-panel.git
        git fetch
        git reset --hard origin/main
    fi
else
    # Fresh clone
    print_status "Cloning repository..."
    git clone https://github.com/Kavis1/vpn-panel.git /opt/vpn-panel/backend || print_error "Failed to clone repository"
    cd /opt/vpn-panel/backend
fi

# Set up Python virtual environment
print_status "Setting up Python virtual environment..."
python3 -m venv /opt/vpn-panel/backend/venv || print_error "Failed to create Python virtual environment"
source /opt/vpn-panel/backend/venv/bin/activate || print_error "Failed to activate virtual environment"
pip install --upgrade pip || print_error "Failed to upgrade pip"

# Install Python dependencies
print_status "Installing Python dependencies..."
python -m pip install --upgrade pip

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt || print_error "Failed to install Python dependencies"
else
    # Install core dependencies directly
    print_status "requirements.txt not found, installing core dependencies..."
    pip install \
        fastapi==0.95.0 \
        uvicorn[standard]==0.22.0 \
        sqlalchemy[asyncio]==2.0.20 \
        alembic==1.12.0 \
        python-jose[cryptography]==3.3.0 \
        passlib[bcrypt]==1.7.4 \
        python-multipart==0.0.6 \
        python-dotenv==1.0.0 \
        psycopg2-binary==2.9.6 \
        python-dateutil==2.8.2 \
        pydantic[email]==1.10.7 \
        python-slugify==8.0.1 \
        typing-extensions==4.5.0 \
        aiosmtplib==2.0.1 \
        jinja2==3.1.2 \
        python-json-logger==2.0.7 \
        pyotp==2.8.0 \
        qrcode==7.4.2 \
        pytz==2023.3 \
        email-validator==2.0.0 \
        || print_error "Failed to install core Python dependencies"
fi

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

# Configure PostgreSQL
print_status "Configuring PostgreSQL..."

# Set default values if not provided
POSTGRES_DB=${POSTGRES_DB:-vpnpanel}
POSTGRES_USER=${POSTGRES_USER:-vpnpanel}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-$(openssl rand -hex 16)}

echo "Database: $POSTGRES_DB"
echo "User: $POSTGRES_USER"

# Check if database exists
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$POSTGRES_DB"; then
    echo "Creating database $POSTGRES_DB..."
    sudo -u postgres psql -c "CREATE DATABASE $POSTGRES_DB;" || print_error "Failed to create database"
    
    echo "Creating user $POSTGRES_USER..."
    sudo -u postgres psql -c "CREATE USER \"$POSTGRES_USER\" WITH PASSWORD '$POSTGRES_PASSWORD';" || print_error "Failed to create database user"
    
    echo "Granting privileges..."
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE \"$POSTGRES_DB\" TO \"$POSTGRES_USER\";" || print_error "Failed to grant privileges"
else
    print_status "Database $POSTGRES_DB already exists, skipping creation..."
    
    # Check if user exists
    if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$POSTGRES_USER'" | grep -q 1; then
        echo "Creating user $POSTGRES_USER..."
        sudo -u postgres psql -c "CREATE USER \"$POSTGRES_USER\" WITH PASSWORD '$POSTGRES_PASSWORD';" || print_status "Warning: Failed to create database user (may already exist)"
    fi
    
    # Ensure user has privileges
    echo "Ensuring privileges for $POSTGRES_USER on $POSTGRES_DB..."
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE \"$POSTGRES_DB\" TO \"$POSTGRES_USER\";" || print_status "Warning: Failed to grant privileges (may already be granted)"
fi

# Update .env with database credentials
sed -i "s/DATABASE_URL=.*/DATABASE_URL=postgresql+asyncpg:\/\/$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432\/$POSTGRES_DB/" /opt/vpn-panel/backend/.env

# Run database migrations
print_status "Running database migrations..."
cd /opt/vpn-panel/backend

# Add current directory to Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Initialize alembic if not already initialized
if [ ! -d "alembic" ]; then
    print_status "Initializing alembic..."
    alembic init alembic || print_error "Failed to initialize alembic"
    
    # Copy our custom env.py if it exists
    if [ -f "alembic.ini.example" ]; then
        cp alembic.ini.example alembic.ini
    fi
    
    # Update alembic.ini with correct database URL
    sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/$POSTGRES_DB|" alembic.ini
    
    # Create versions directory
    mkdir -p alembic/versions
    touch alembic/versions/.gitkeep
    
    # Create initial migration
    print_status "Creating initial migration..."
    PYTHONPATH=$(pwd) alembic revision --autogenerate -m "Initial migration" || print_status "Warning: Failed to create initial migration (tables may already exist)"
fi

# Run migrations
print_status "Running migrations..."
PYTHONPATH=$(pwd) alembic upgrade head || print_status "Warning: Failed to run database migrations (tables may already be up to date)"

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
