# Monitoring

## Overview of Monitoring

The monitoring system provides a comprehensive overview of the state of your VPN infrastructure in real-time. Monitoring includes:

- **Server Status**
- **Resource Usage** (CPU, RAM, disk space)
- **Network Activity**
- **User Statistics**
- **VPN Connection Performance**

## Monitoring Panel

### Main Widgets:
1. **General Statistics**
   - Number of active users
   - Total traffic (incoming/outgoing)
   - Average server load

2. **Real-time Charts**
   - CPU usage
   - RAM usage
   - Network traffic
   - Number of connections

3. **Service Status**
   - Xray-core
   - API server
   - Database
   - Cache

## Alert Configuration

### Alert Types:
1. **Critical** (requires immediate attention)
   - Server failure
   - Critical CPU/RAM load
   - Disk space filling

2. **Warnings** (requires monitoring)
   - High resource usage
   - Suspicious activity
   - Log errors

### Notification Channels:
- Email
- Telegram
- Slack
- Webhook

## Integration with External Systems

### Prometheus + Grafana

1. **Installing the Metrics Exporter**
   ```bash
   # Installing node_exporter
   wget https://github.com/prometheus/node_exporter/releases/download/v1.3.1/node_exporter-1.3.1.linux-amd64.tar.gz
   tar xvfz node_exporter-1.3.1.linux-amd64.tar.gz
   cd node_exporter-1.3.1.linux-amd64/
   sudo cp node_exporter /usr/local/bin/
   ```

2. **Configuring the systemd Service**
   ```ini
   [Unit]
   Description=Node Exporter
   After=network.target

   [Service]
   User=node_exporter
   Group=node_exporter
   Type=simple
   ExecStart=/usr/local/bin/node_exporter

   [Install]
   WantedBy=multi-user.target
   ```

3. **Importing the Dashboard into Grafana**
   - Import the dashboard with ID 1860
   - Configure the Prometheus data source

## Log Analysis

### Main Logs for Monitoring:
- `/var/log/xray/error.log`
- `/var/log/syslog`
- `/var/log/auth.log`
- Application logs

### Configuring Centralized Log Collection:
```yaml
# Example Filebeat configuration for sending logs to ELK
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/xray/*.log
  fields:
    app: vpn-panel
    environment: production

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  indices:
    - index: "vpn-panel-%{+yyyy.MM.dd}"
```

## Security Monitoring

### Key Security Metrics:
1. **Authentication**
   - Failed login attempts
   - Suspicious IP addresses
   - Password guessing attempts

2. **Network Attacks**
   - Port scanning
   - DDoS attacks
   - Suspicious traffic patterns

### Configuring Fail2Ban:
```ini
[vpn-panel]
enabled = true
port = http,https
filter = vpn-panel
logpath = /var/log/vpn-panel/access.log
maxretry = 5
findtime = 600
bantime = 3600
```

## Performance and Scaling

### Monitoring Recommendations:
1. **Basic Metrics**
   - API response time
   - Database query execution time
   - Connection usage

2. **Load Testing**
   - Conduct regular load tests
   - Monitor performance under load
   - Identify bottlenecks

### Example Load Test Configuration:
```yaml
scenarios:
  vpn_api_test:
    executor: constant-vus
    vus: 100
    duration: 5m
    gracefulStop: 30s
    env:
      BASE_URL: https://api.vpn-panel.example.com
    stages:
      - duration: '1m'
        target: 100
      - duration: '3m'
        target: 500
      - duration: '1m'
        target: 0
```

## Backup of Monitoring Data

### Recommended Strategy:
1. Daily full backup of metrics
2. Weekly archiving of logs
3. Store backups for at least 90 days

### Example Backup Script:
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/monitoring"
DATE=$(date +%Y%m%d)

# Create a backup of Prometheus data
sudo systemctl stop prometheus
sudo tar -czf "$BACKUP_DIR/prometheus-$DATE.tar.gz" /var/lib/prometheus
sudo systemctl start prometheus

# Rotate old backups
find "$BACKUP_DIR" -type f -mtime +90 -delete
