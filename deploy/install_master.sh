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

# Auto-generate admin credentials only
ADMIN_USERNAME="admin_$(openssl rand -hex 3)"
ADMIN_PASSWORD="$(openssl rand -base64 12 | tr -d '=+/' | cut -c1-16)"

# Get user input for domain and email
read -p "Enter your domain name (or press Enter to use IP address): " DOMAIN
read -p "Enter admin email (for Let's Encrypt): " EMAIL

# Set default domain to IP if not provided
if [ -z "$DOMAIN" ]; then
    DOMAIN=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')
    print_status "Using detected IP address as domain: $DOMAIN"
fi

# Save credentials to a file
mkdir -p /etc/vpn-panel
echo "ADMIN_USERNAME=$ADMIN_USERNAME" > /etc/vpn-panel/credentials
echo "ADMIN_PASSWORD=$ADMIN_PASSWORD" >> /etc/vpn-panel/credentials
echo "ADMIN_EMAIL=$EMAIL" >> /etc/vpn-panel/credentials
echo "DOMAIN=$DOMAIN" >> /etc/vpn-panel/credentials
chmod 600 /etc/vpn-panel/credentials

print_success "Generated admin username: $ADMIN_USERNAME"
print_success "Generated admin password: $ADMIN_PASSWORD"
print_success "Admin email: $EMAIL"
print_success "Domain: $DOMAIN"

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

# Install uvicorn first with explicit path and verify installation
print_status "Installing uvicorn and core dependencies..."
pip install --no-cache-dir --upgrade pip || print_error "Failed to upgrade pip"
pip install --no-cache-dir uvicorn[standard]==0.22.0 gunicorn==20.1.0 || print_error "Failed to install uvicorn and gunicorn"

# Verify uvicorn installation
if ! command -v uvicorn &> /dev/null; then
    print_status "uvicorn not found in PATH, checking installation..."
    python -m pip install --no-cache-dir uvicorn[standard]==0.22.0 || print_error "Failed to install uvicorn"
    
    # Create symlink if needed
    if [ ! -f "/usr/local/bin/uvicorn" ] && [ -f "/usr/local/bin/uvicorn3" ]; then
        ln -s /usr/local/bin/uvicorn3 /usr/local/bin/uvicorn
    fi
    
    # Verify again
    if ! command -v uvicorn &> /dev/null; then
        print_error "Failed to install uvicorn. Please check your Python environment."
    fi
fi

# Install requirements from requirements.txt if it exists
if [ -f "requirements.txt" ]; then
    print_status "Installing requirements from requirements.txt..."
    pip install --no-cache-dir -r requirements.txt || print_status "Warning: Some requirements could not be installed"
    
    # Install any remaining dependencies
    if [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
        print_status "Installing package in development mode..."
        pip install --no-cache-dir -e . || print_status "Warning: Could not install in development mode"
    fi
fi
    
    # Generate a compiled requirements file with all dependencies
    print_status "Checking for missing dependencies..."
    pip-compile --quiet --output-file="$TEMP_DIR/requirements_compiled.txt" requirements.txt
    
    # Install missing packages only
    while IFS= read -r pkg; do
        # Skip empty lines and comments
        if [ -z "$pkg" ] || [[ "$pkg" == "#"* ]]; then
            continue
        fi
        
        # Extract package name (handling different requirement formats)
        pkg_name=$(echo "$pkg" | grep -o '^[^<>=!; ]*' | tr '[:upper:]' '[:lower:]')
        
        # Skip if package name is empty
        if [ -z "$pkg_name" ]; then
            continue
        fi
        
        # Check if package is already installed
        if ! pip show "$pkg_name" &>/dev/null; then
            print_status "Installing $pkg_name..."
            pip install --no-cache-dir "$pkg" || print_status "Warning: Failed to install $pkg_name"
        fi
    done < "$TEMP_DIR/requirements_compiled.txt"
    
    # Clean up
    rm -rf "$TEMP_DIR"
else
    print_status "No requirements.txt found, skipping requirements installation"
fi

# Create and activate virtual environment
if [ ! -d "/opt/vpn-panel/backend/venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv /opt/vpn-panel/backend/venv || print_error "Failed to create virtual environment"
    
    # Activate virtual environment
    print_status "Activating Python virtual environment..."
    source /opt/vpn-panel/backend/venv/bin/activate || print_error "Failed to activate virtual environment"
    
    # Install core dependencies
    print_status "Installing core Python dependencies..."
    pip install --upgrade pip || print_status "Warning: Failed to upgrade pip"
    pip install alembic psycopg2-binary sqlalchemy || print_error "Failed to install database dependencies"
else
    # Activate existing virtual environment
    source /opt/vpn-panel/backend/venv/bin/activate || print_error "Failed to activate existing virtual environment"
fi



# Run database migrations
print_status "Running database migrations..."

# Create migrations directory if it doesn't exist
mkdir -p /opt/vpn-panel/backend/migrations

# Initialize alembic if not already initialized
if [ ! -f "alembic.ini" ]; then
    print_status "Initializing alembic..."
    
    # Ensure we're using the correct Python and pip
    PYTHON_PATH=$(which python3)
    PIP_PATH=$(which pip)
    print_status "Using Python: $PYTHON_PATH"
    print_status "Using pip: $PIP_PATH"
    
    # Try multiple approaches to initialize alembic
    if ! PYTHONPATH=$PYTHONPATH:. $PYTHON_PATH -m alembic init alembic; then
        print_status "First attempt failed, trying alternative approach..."
        if ! PYTHONPATH=$PYTHONPATH:. /opt/vpn-panel/backend/venv/bin/python -m alembic init alembic; then
            print_status "Second attempt failed, trying with full path..."
            if [ -f "/opt/vpn-panel/backend/venv/bin/alembic" ]; then
                /opt/vpn-panel/backend/venv/bin/alembic init alembic || 
                print_error "Failed to initialize alembic after multiple attempts"
            else
                print_error "Alembic executable not found in venv/bin/"
            fi
        fi
    fi
    
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

# Try multiple approaches to run migrations
print_status "Running database migrations..."

# Set full path to Python and alembic
PYTHON_BIN="/opt/vpn-panel/backend/venv/bin/python"
ALEMBIC_BIN="/opt/vpn-panel/backend/venv/bin/alembic"

# Try multiple approaches to run migrations
if [ -f "$ALEMBIC_BIN" ]; then
    print_status "Running migrations using $ALEMBIC_BIN..."
    PYTHONPATH=$PYTHONPATH:. $ALEMBIC_BIN upgrade head || {
        print_status "First attempt failed, trying alternative approach..."
        PYTHONPATH=$PYTHONPATH:. $PYTHON_BIN -m alembic upgrade head || {
            print_status "Second attempt failed, trying with system Python..."
            PYTHONPATH=$PYTHONPATH:. python3 -m alembic upgrade head || 
            print_error "Failed to run database migrations after multiple attempts"
        }
    }
else
    print_error "Alembic binary not found at $ALEMBIC_BIN"
    print_status "Trying to install alembic globally..."
    pip install alembic && PYTHONPATH=$PYTHONPATH:. alembic upgrade head || 
    print_error "Failed to run database migrations"
fi

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
print_success "\n==================================================\n"

echo "Installation completed successfully!"
exit 0
