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

# Auto-generate admin credentials
ADMIN_USERNAME="admin_$(openssl rand -hex 3)"
ADMIN_PASSWORD="$(openssl rand -base64 12 | tr -d '=+/' | cut -c1-16)"

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

# Set up VPN Panel repository
print_status "Setting up VPN Panel repository..."
mkdir -p /opt/vpn-panel/backend
cd /opt/vpn-panel/backend

# Clone repository with full history
print_status "Cloning repository..."
git clone --depth 1 --no-single-branch https://github.com/Kavis1/vpn-panel.git . || print_error "Failed to clone repository"

# Ensure we have all files
print_status "Ensuring all files are checked out..."
git fetch --unshallow || true
git fetch --all
git reset --hard origin/main

# Debug: List files after clone
print_status "Contents after git clone:"
ls -la || true


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

# Set up Python path
export PYTHONPATH=/opt/vpn-panel/backend:$PYTHONPATH
cd /opt/vpn-panel/backend

# Install the package in development mode
print_status "Checking if package is already installed..."
cd /opt/vpn-panel/backend

# Check if the package is already installed
if python3 -c "import app" &>/dev/null; then
    print_status "Package is already installed, skipping installation..."
else
    # Debug: List files in backend directory
    print_status "Contents of /opt/vpn-panel/backend:"
    ls -la || true

    # Try installing in development mode if package files exist
    if [ -f "setup.py" ]; then
        print_status "Found setup.py, checking if installation is needed..."
        if ! python3 -c "import app" &>/dev/null; then
            print_status "Installing in development mode..."
            pip install -e . || {
                print_status "Warning: Development mode installation failed, trying with --no-deps..."
                pip install -e . --no-deps || print_status "Warning: Development mode with --no-deps failed"
            }
        else
            print_status "Package is already installed, skipping..."
        fi
    elif [ -f "pyproject.toml" ]; then
        print_status "Found pyproject.toml, checking if installation is needed..."
        if ! python3 -c "import app" &>/dev/null; then
            print_status "Installing in development mode..."
            pip install -e . || {
                print_status "Warning: Development mode installation failed, trying with --no-deps..."
                pip install -e . --no-deps || print_status "Warning: Development mode with --no-deps failed"
            }
        else
            print_status "Package is already installed, skipping..."
        fi
    else
        print_status "Warning: No setup.py or pyproject.toml found in /opt/vpn-panel/backend"
        print_status "Falling back to regular installation..."
    fi
fi

# Function to check if a Python package is installed
is_package_installed() {
    python3 -c "import $1" 2>/dev/null
    return $?
}

# Generate random admin credentials if not set
if [ -z "$ADMIN_USERNAME" ]; then
    ADMIN_USERNAME="admin_$(openssl rand -hex 3)"
    ADMIN_PASSWORD="$(openssl rand -base64 12 | tr -d '=+/' | cut -c1-16)"
    export ADMIN_USERNAME ADMIN_PASSWORD
    
    # Save credentials to a file
    mkdir -p /etc/vpn-panel
    echo "ADMIN_USERNAME=$ADMIN_USERNAME" > /etc/vpn-panel/credentials
    echo "ADMIN_PASSWORD=$ADMIN_PASSWORD" >> /etc/vpn-panel/credentials
    chmod 600 /etc/vpn-panel/credentials
    
    print_status "Generated admin username: $ADMIN_USERNAME"
    print_status "Generated admin password: $ADMIN_PASSWORD"
    print_status "Credentials saved to /etc/vpn-panel/credentials"
fi

# Generate random panel path if not set
if [ -z "$PANEL_PATH" ]; then
    PANEL_PATH="/panel_$(openssl rand -hex 8)"
    export PANEL_PATH
    
    # Save panel path to a file
    echo "PANEL_PATH=$PANEL_PATH" > /etc/vpn-panel/panel_path
    chmod 644 /etc/vpn-panel/panel_path
    
    print_status "Generated panel path: $PANEL_PATH"
fi

# Update .env with generated values
if [ -f "/opt/vpn-panel/backend/.env" ]; then
    sed -i "s/^FIRST_SUPERUSER=.*/FIRST_SUPERUSER=$ADMIN_USERNAME/" /opt/vpn-panel/backend/.env
    sed -i "s/^FIRST_SUPERUSER_PASSWORD=.*/FIRST_SUPERUSER_PASSWORD=$ADMIN_PASSWORD/" /opt/vpn-panel/backend/.env
    sed -i "s|^PANEL_PATH=.*|PANEL_PATH=$PANEL_PATH|" /opt/vpn-panel/backend/.env
fi

# Install requirements directly from requirements.txt if it exists
if [ -f "requirements.txt" ]; then
    print_status "Checking and installing requirements from requirements.txt..."
    
    # Create a temporary directory for package checking
    TEMP_DIR=$(mktemp -d)
    
    # Install pip-tools if not installed
    if ! command -v pip-compile &> /dev/null; then
        print_status "Installing pip-tools for dependency management..."
        pip install --no-cache-dir pip-tools || print_error "Failed to install pip-tools"
    fi
    
    # Generate a compiled requirements file with all dependencies
    print_status "Checking for missing dependencies..."
    pip-compile --quiet --output-file="$TEMP_DIR/requirements_compiled.txt" requirements.txt
    
    # Install missing packages only
    while IFS= read -r pkg; do
        # Extract package name (handling different requirement formats)
        pkg_name=$(echo "$pkg" | grep -o '^[^<>=!; ]*' | tr '[:upper:]' '[:lower:]')
        
        # Skip empty lines and comments
        [ -z "$pkg_name" ] && continue
        [[ "$pkg_name" == "#"* ]] && continue
        
        # Check if package is already installed
        if ! is_package_installed "$pkg_name"; then
            print_status "Installing missing package: $pkg_name"
            pip install --no-cache-dir "$pkg" || print_status "Warning: Failed to install $pkg"
        else
            print_status "Package already installed: $pkg_name"
        fi
    done < "$TEMP_DIR/requirements_compiled.txt"
    
    # Clean up
    rm -rf "$TEMP_DIR"
else
    print_status "No requirements.txt found, skipping requirements installation"
fi

# Run database migrations
print_status "Running database migrations..."

# Create migrations directory if it doesn't exist
mkdir -p /opt/vpn-panel/backend/migrations

# Initialize alembic if not already initialized
if [ ! -f "alembic.ini" ]; then
    print_status "Initializing alembic..."
    alembic init alembic || print_error "Failed to initialize alembic"
    
    # Copy our custom env.py if it exists
    if [ -f "alembic.ini.example" ]; then
        cp alembic.ini.example alembic.ini
    fi
    
    # Update alembic.ini with correct database URL
    sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/$POSTGRES_DB|" alembic.ini
    
    # Update env.py to use our models
    sed -i "s|from logging.config import fileConfig|import os\nimport sys\nfrom logging.config import fileConfig\n\n# Add the backend directory to the Python path\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n\nfrom app.db.base import Base\nfrom app.core.config import settings\n\n# Use the same metadata for 'target_metadata'\ntarget_metadata = Base.metadata\n|g" alembic/env.py
    
    # Create versions directory
    mkdir -p alembic/versions
    touch alembic/versions/.gitkeep
    
    # Create initial migration
    print_status "Creating initial migration..."
    PYTHONPATH=/opt/vpn-panel/backend alembic revision --autogenerate -m "Initial migration" || print_status "Warning: Failed to create initial migration (tables may already exist)"
fi

# Run migrations
print_status "Running migrations..."
cd /opt/vpn-panel/backend
export PYTHONPATH=$PYTHONPATH:$(pwd)
alembic upgrade head || print_status "Warning: Failed to run database migrations (tables may already be up to date)"

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

# Create Nginx directories if they don't exist
mkdir -p /etc/nginx/sites-available
mkdir -p /etc/nginx/sites-enabled

# Create Nginx configuration with random path
cat > /etc/nginx/sites-available/vpn-panel << EOL
server {
    listen 80;
    listen [::]:80;
    server_name _;
    return 301 https://\$host$PANEL_PATH;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name _;

    ssl_certificate /etc/letsencrypt/live/\$host/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/\$host/privkey.pem;

    # Deny access to hidden files
    location ~ /\. {
        deny all;
        return 404;
    }

    # Main application
    location $PANEL_PATH {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Script-Name $PANEL_PATH;
        proxy_redirect / $PANEL_PATH/;
    }

    # Redirect root to panel path
    location = / {
        return 301 $PANEL_PATH;
    }
}
EOL

# Enable site
ln -sf /etc/nginx/sites-available/vpn-panel /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

# Test Nginx configuration
nginx -t || print_status "Warning: Nginx configuration test failed"

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

# Create a Python script to create admin user
cat > /opt/vpn-panel/backend/create_admin.py << 'EOL'
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.core.config import settings
from app.models.user import User
from app.core.security import get_password_hash

def create_admin_user():
    db = SessionLocal()
    try:
        # Check if admin user already exists
        admin = db.query(User).filter(User.email == 'admin@example.com').first()
        if not admin:
            admin = User(
                email='admin@example.com',
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD or 'admin'),
                is_superuser=True,
                is_active=True,
                is_verified=True
            )
            db.add(admin)
            db.commit()
            print('Admin user created successfully')
            return True
        else:
            print('Admin user already exists')
            return True
    except Exception as e:
        print(f'Error creating admin user: {str(e)}')
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == '__main__':
    if create_admin_user():
        sys.exit(0)
    else:
        sys.exit(1)
EOL

# Run the script with the correct Python path
cd /opt/vpn-panel/backend
export PYTHONPATH=$PYTHONPATH:$(pwd)
python create_admin.py || print_status "Warning: Failed to create admin user (user may already exist)"

# Clean up
rm -f /opt/vpn-panel/backend/create_admin.py

# Print installation summary
print_success "\n=================================================="
print_success "  VPN Panel Installation Complete"
print_success "=================================================="
print_success "\nAccess the VPN Panel at: https://$(curl -s ifconfig.me)$PANEL_PATH"
print_success "Generated admin username: $ADMIN_USERNAME"
print_success "Generated admin password: $ADMIN_PASSWORD"
print_success "Admin email: $EMAIL"
print_success "Domain: $DOMAIN"

# Save credentials to a file
mkdir -p /etc/vpn-panel
echo "ADMIN_USERNAME=$ADMIN_USERNAME" > /etc/vpn-panel/credentials
echo "ADMIN_PASSWORD=$ADMIN_PASSWORD" >> /etc/vpn-panel/credentials
echo "ADMIN_EMAIL=$EMAIL" >> /etc/vpn-panel/credentials
echo "DOMAIN=$DOMAIN" >> /etc/vpn-panel/credentials
chmod 600 /etc/vpn-panel/credentials
print_success "\nIMPORTANT: Please save these credentials in a secure location!"
print_success "Credentials are also saved to: /etc/vpn-panel/credentials"
print_success "\nTo start the VPN Panel service:"
print_success "  sudo systemctl start vpn-panel"
print_success "\nTo view logs:"
print_success "  sudo journalctl -u vpn-panel -f"
print_success "\nTo change the admin password:"
print_success "  1. Log in to the panel"
print_success "  2. Go to Admin -> Users"
print_success "  3. Click on your username"
print_success "  4. Click 'Change Password'"
print_success "\n==================================================\n"Installation completed successfully!
