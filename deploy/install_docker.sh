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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_status "Docker is not installed. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    print_success "Docker installed successfully"
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_status "Docker Compose is not installed. Installing Docker Compose..."
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'"' -f4)
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed successfully"
fi

# Get user input
read -p "Enter your domain name (or press Enter to use IP address): " USER_DOMAIN
read -p "Enter admin email (for Let's Encrypt): " USER_EMAIL

# Set default domain to IP if not provided
if [ -z "$USER_DOMAIN" ]; then
    USER_DOMAIN=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')
    print_status "Using detected IP address as domain: $USER_DOMAIN"
fi

# Set domain and email variables
export DOMAIN="$USER_DOMAIN"
export EMAIL="$USER_EMAIL"

# Generate random passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -hex 32)
ADMIN_PASSWORD=$(openssl rand -base64 16 | tr -d '=+/' | cut -c1-16)

# Create .env file
print_status "Creating .env file..."
cat > .env << EOL
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=vpn_panel
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Application
SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=${DOMAIN},localhost,127.0.0.1
TIME_ZONE=UTC

# First superuser
FIRST_SUPERUSER=admin
FIRST_SUPERUSER_PASSWORD=${ADMIN_PASSWORD}
FIRST_SUPERUSER_EMAIL=${EMAIL}

# Xray
XRAY_API_HOST=xray
XRAY_API_PORT=10085
XRAY_EXECUTABLE_PATH=/usr/local/bin/xray

# Traefik
TRAEFIK_ACME_EMAIL=${EMAIL}
DOMAIN=${DOMAIN}
EOL

print_success ".env file created with secure credentials"

# Clone the repository if not already present
if [ ! -d "vpn-panel" ]; then
    print_status "Cloning VPN Panel repository..."
    git clone https://github.com/Kavis1/vpn-panel.git
    cd vpn-panel
else
    print_status "Updating existing VPN Panel installation..."
    cd vpn-panel
    git pull
fi

# Copy .env to the project root
cp .env .

# Pull and start services
print_status "Starting VPN Panel with Docker Compose..."
docker-compose -f docker-compose.yml up -d --build

# Wait for services to start
print_status "Waiting for services to initialize (this may take a few minutes)..."
sleep 30

# Show status
print_status "Checking containers status..."
docker-compose -f docker-compose.yml ps

# Check if the web service is running
if docker-compose -f docker-compose.yml ps | grep -q "Up"; then
    print_success "VPN Panel is now running!"
    echo ""
    echo "==============================================="
    echo "          VPN Panel Installation Complete"
    echo "==============================================="
    echo ""
    echo "Admin Panel: http://${DOMAIN}:8000"
    echo "Username: admin"
    echo "Password: ${ADMIN_PASSWORD}"
    echo ""
    echo "Important: Change the admin password after first login!"
    echo ""
    echo "==============================================="
    echo ""
    
    # Save credentials
    mkdir -p /etc/vpn-panel
    echo "ADMIN_USERNAME=admin" > /etc/vpn-panel/credentials
    echo "ADMIN_PASSWORD=${ADMIN_PASSWORD}" >> /etc/vpn-panel/credentials
    echo "ADMIN_EMAIL=${EMAIL}" >> /etc/vpn-panel/credentials
    echo "DOMAIN=${DOMAIN}" >> /etc/vpn-panel/credentials
    chmod 600 /etc/vpn-panel/credentials
    
    print_success "Installation completed successfully!"
    print_status "You can manage the VPN Panel with the following commands:"
    echo "  Start:   cd /root/vpn-panel && docker-compose up -d"
    echo "  Stop:    cd /root/vpn-panel && docker-compose down"
    echo "  Logs:    cd /root/vpn-panel && docker-compose logs -f"
    echo "  Upgrade: cd /root/vpn-panel && git pull && docker-compose up -d --build"
    echo ""
else
    print_error "Failed to start VPN Panel. Please check the logs with: docker-compose logs"
fi
