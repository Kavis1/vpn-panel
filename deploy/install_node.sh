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
read -p "Enter master server domain or IP: " MASTER_SERVER
read -p "Enter node name: " NODE_NAME
read -p "Enter node token (get from master admin panel): " NODE_TOKEN
read -p "Enter node IP (press Enter to auto-detect): " NODE_IP

# Set default values if not provided
[ -z "$NODE_IP" ] && NODE_IP=$(hostname -I | awk '{print $1}')

print_status "Starting VPN Panel Node installation..."

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
apt-get install -y curl wget ufw || print_error "Failed to install required packages"

# Configure firewall
print_status "Configuring firewall..."
ufw allow 22/tcp
ufw allow 443/tcp
ufw allow 80/tcp
ufw --force enable || print_warning "Failed to enable UFW"

# Install Xray
print_status "Installing Xray..."
wget -O /tmp/xray.zip https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip || print_error "Failed to download Xray"
unzip /tmp/xray.zip -d /tmp/xray || print_error "Failed to extract Xray"
install -m 755 /tmp/xray/xray /usr/local/bin/ || print_error "Failed to install Xray"
rm -rf /tmp/xray /tmp/xray.zip

# Create Xray config directory
mkdir -p /etc/xray

# Create systemd service for Xray
print_status "Creating Xray service..."
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

# Generate node configuration
print_status "Generating node configuration..."
NODE_ID=$(cat /proc/sys/kernel/random/uuid)
XRAY_UUID=$(cat /proc/sys/kernel/random/uuid)

# Create Xray config
cat > /etc/xray/config.json << EOL
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
            "id": "${XRAY_UUID}",
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
              "certificateFile": "/etc/xray/cert.pem",
              "keyFile": "/etc/xray/key.pem"
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
  ]
}
EOL

# Create node registration script
print_status "Creating node registration script..."
cat > /usr/local/bin/register-node.sh << 'EOL'
#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load environment variables
[ -f /etc/default/vpn-node ] && . /etc/default/vpn-node

# Check if required variables are set
if [ -z "$MASTER_SERVER" ] || [ -z "$NODE_TOKEN" ] || [ -z "$NODE_NAME" ] || [ -z "$NODE_IP" ]; then
    echo -e "${RED}Error: Required environment variables not set.${NC}"
    echo "Please set MASTER_SERVER, NODE_TOKEN, NODE_NAME, and NODE_IP in /etc/default/vpn-node"
    exit 1
fi

# Generate self-signed certificate if not exists
if [ ! -f "/etc/xray/cert.pem" ] || [ ! -f "/etc/xray/key.pem" ]; then
    echo -e "${YELLOW}Generating self-signed certificate...${NC}"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/xray/key.pem \
        -out /etc/xray/cert.pem \
        -subj "/CN=$NODE_IP" || { echo -e "${RED}Failed to generate certificate${NC}"; exit 1; }
    chmod 600 /etc/xray/*.pem
fi

# Register node with master
echo -e "${YELLOW}Registering node with master server...${NC}"
RESPONSE=$(curl -s -X POST "https://$MASTER_SERVER/api/v1/nodes/register" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$NODE_NAME\",\"ip\":\"$NODE_IP\",\"token\":\"$NODE_TOKEN\"}")

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to connect to master server${NC}"
    exit 1
fi

# Check if registration was successful
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo -e "${GREEN}Node registered successfully!${NC}"
    
    # Save node configuration
    NODE_ID=$(echo "$RESPONSE" | grep -oP '(?<="node_id":")[^"]+')
    XRAY_CONFIG=$(echo "$RESPONSE" | grep -oP '(?<="xray_config":").*?(?=\u0022\}'")')
    
    echo "NODE_ID=$NODE_ID" > /etc/default/vpn-node
    echo "MASTER_SERVER=$MASTER_SERVER" >> /etc/default/vpn-node
    echo "NODE_NAME='$NODE_NAME'" >> /etc/default/vpn-node
    echo "NODE_IP=$NODE_IP" >> /etc/default/vpn-node
    echo "NODE_TOKEN=$NODE_TOKEN" >> /etc/default/vpn-node
    
    # Update Xray config
    echo "$XRAY_CONFIG" | base64 -d > /etc/xray/config.json
    
    # Restart Xray
    systemctl restart xray
    
    echo -e "${GREEN}Xray configuration updated and service restarted.${NC}"
else
    ERROR_MSG=$(echo "$RESPONSE" | grep -oP '(?<="message":")[^"]+')
    echo -e "${RED}Registration failed: $ERROR_MSG${NC}"
    exit 1
fi
EOL

# Make registration script executable
chmod +x /usr/local/bin/register-node.sh

# Create environment file
print_status "Creating environment file..."
cat > /etc/default/vpn-node << EOL
# VPN Node Configuration
MASTER_SERVER=$MASTER_SERVER
NODE_NAME='$NODE_NAME'
NODE_IP=$NODE_IP
NODE_TOKEN=$NODE_TOKEN
EOL

# Create systemd service for node registration
print_status "Creating node registration service..."
cat > /etc/systemd/system/vpn-node-register.service << 'EOL'
[Unit]
Description=VPN Node Registration
After=network.target

[Service]
Type=oneshot
EnvironmentFile=/etc/default/vpn-node
ExecStart=/usr/local/bin/register-node.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOL

# Create systemd timer for periodic registration
cat > /etc/systemd/system/vpn-node-register.timer << 'EOL'
[Unit]
Description=VPN Node Registration Timer

[Timer]
OnBootSec=5min
OnUnitActiveSec=1h

[Install]
WantedBy=timers.target
EOL

# Enable and start services
print_status "Starting services..."
systemctl daemon-reload
systemctl enable xray vpn-node-register.timer
systemctl start xray vpn-node-register || print_error "Failed to start services"
systemctl start vpn-node-register.timer

# Initial registration
print_status "Performing initial node registration..."
/usr/local/bin/register-node.sh || print_error "Failed to register node"

# Print installation summary
print_success "\n=================================================="
print_success "  VPN Panel Node Installation Complete"
print_success "=================================================="
echo -e "\n${GREEN}Node Name:${NC} $NODE_NAME"
echo -e "${GREEN}Node IP:${NC} $NODE_IP"
echo -e "${GREEN}Master Server:${NC} $MASTER_SERVER"
echo -e "\n${YELLOW}Node will automatically register with the master server every hour.${NC}"

print_success "\nInstallation completed successfully!"
