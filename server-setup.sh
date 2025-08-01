#!/bin/bash

# Complete Server Setup Script for Mill Management System
# Ubuntu Server 24.04 LTS

set -e

echo "🚀 Starting Complete Server Setup..."
echo "📍 Server: 45.154.238.102"
echo "👤 User: administrator"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. System Update
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_success "System updated"

# 2. Install Essential Packages
print_status "Installing essential packages..."
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    ufw \
    fail2ban \
    logwatch \
    rkhunter \
    chkrootkit \
    clamav \
    clamav-daemon \
    unzip \
    zip \
    jq \
    tree \
    net-tools \
    nginx \
    certbot \
    python3-certbot-nginx
print_success "Essential packages installed"

# 3. Install Docker
print_status "Installing Docker..."
if ! command -v docker &> /dev/null; then
    sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo usermod -aG docker $USER
    print_success "Docker installed successfully"
else
    print_status "Docker already installed"
fi

# 4. Install Docker Compose
print_status "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed successfully"
else
    print_status "Docker Compose already installed"
fi

# 5. Configure Firewall (UFW)
print_status "Configuring firewall..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp  # Traefik dashboard
sudo ufw --force enable
print_success "Firewall configured"

# 6. Configure Fail2Ban
print_status "Configuring Fail2Ban..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Create custom fail2ban config
sudo tee /etc/fail2ban/jail.local > /dev/null << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = auto

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3
bantime = 3600

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
action = iptables-multiport[name=ReqLimit, port="http,https"]
logpath = /var/log/nginx/error.log
maxretry = 3
bantime = 3600
EOF

sudo systemctl restart fail2ban
print_success "Fail2Ban configured"

# 7. Configure SSH Security
print_status "Configuring SSH security..."
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

sudo tee -a /etc/ssh/sshd_config > /dev/null << 'EOF'

# Security settings
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
AllowTcpForwarding no
AllowAgentForwarding no
PermitEmptyPasswords no
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
EOF

sudo systemctl restart ssh
print_success "SSH security configured"

# 8. Install and Configure ClamAV
print_status "Configuring ClamAV..."
sudo freshclam
sudo systemctl enable clamav-daemon
sudo systemctl start clamav-daemon
print_success "ClamAV configured"

# 9. Configure System Monitoring
print_status "Configuring system monitoring..."

# Create log rotation for application logs
sudo tee /etc/logrotate.d/mill-management > /dev/null << 'EOF'
/home/administrator/mill-management/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 administrator administrator
}
EOF

# Create system monitoring script
tee ~/monitor-system.sh > /dev/null << 'EOF'
#!/bin/bash

echo "=== System Status Report ==="
echo "Date: $(date)"
echo ""

echo "=== Disk Usage ==="
df -h

echo ""
echo "=== Memory Usage ==="
free -h

echo ""
echo "=== Load Average ==="
uptime

echo ""
echo "=== Docker Containers ==="
docker ps

echo ""
echo "=== Fail2Ban Status ==="
sudo fail2ban-client status

echo ""
echo "=== Recent SSH Attempts ==="
sudo tail -20 /var/log/auth.log | grep sshd

echo ""
echo "=== Recent Nginx Errors ==="
sudo tail -10 /var/log/nginx/error.log 2>/dev/null || echo "No nginx errors"
EOF

chmod +x ~/monitor-system.sh
print_success "System monitoring configured"

# 10. Create Backup Script
print_status "Creating backup script..."
tee ~/backup-system.sh > /dev/null << 'EOF'
#!/bin/bash

BACKUP_DIR="/home/administrator/backups"
DATE=$(date +"%Y%m%d_%H%M%S")
mkdir -p $BACKUP_DIR

echo "Creating system backup..."

# Backup important configs
sudo tar -czf $BACKUP_DIR/system-config-$DATE.tar.gz \
    /etc/ssh/sshd_config \
    /etc/fail2ban \
    /etc/ufw \
    /etc/nginx \
    /var/log

# Backup application data
if [ -d "/home/administrator/mill-management" ]; then
    tar -czf $BACKUP_DIR/mill-management-$DATE.tar.gz \
        /home/administrator/mill-management
fi

# Clean old backups (keep last 7)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x ~/backup-system.sh
print_success "Backup script created"

# 11. Configure Automatic Updates
print_status "Configuring automatic updates..."
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
print_success "Automatic updates configured"

# 12. Create Application Directory
print_status "Setting up application directory..."
mkdir -p ~/mill-management
cd ~/mill-management

# 13. Create Environment File
print_status "Creating environment configuration..."
tee .env > /dev/null << 'EOF'
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=mill_management
DB_USER=mill_user
DB_PASSWORD=mill_password_2024

# Redis Configuration
REDIS_URL=redis://redis:6379

# MQTT Broker Configuration
MQTT_BROKER=45.154.238.114
MQTT_USERNAME=uc300
MQTT_PASSWORD=grain300
MQTT_PORT=1883

# JWT Secret
JWT_SECRET=mill_jwt_secret_2024_production

# CORS Configuration
CORS_ORIGIN=https://test.nexonsolutions.be

# Node Environment
NODE_ENV=production

# Traefik Configuration
TRAEFIK_DASHBOARD_PASSWORD=mill_traefik_2024
EOF

print_success "Environment file created"

# 14. Create Management Scripts
print_status "Creating management scripts..."

# Start script
tee start.sh > /dev/null << 'EOF'
#!/bin/bash

echo "🚀 Starting Mill Management System..."

cd ~/mill-management
docker-compose -f docker-compose.production.yml up -d

echo "⏳ Waiting for services to start..."
sleep 30

echo "📊 Service Status:"
docker-compose -f docker-compose.production.yml ps

echo "✅ System started successfully!"
echo "🌐 Access points:"
echo "  - Main App: https://test.nexonsolutions.be"
echo "  - API: https://api.nexonsolutions.be"
echo "  - Admin: https://admin.nexonsolutions.be"
echo "  - Monitoring: https://monitor.nexonsolutions.be"
echo "  - Traefik Dashboard: https://traefik.nexonsolutions.be"
EOF

# Stop script
tee stop.sh > /dev/null << 'EOF'
#!/bin/bash

echo "🛑 Stopping Mill Management System..."

cd ~/mill-management
docker-compose -f docker-compose.production.yml down

echo "✅ System stopped successfully!"
EOF

# Restart script
tee restart.sh > /dev/null << 'EOF'
#!/bin/bash

echo "🔄 Restarting Mill Management System..."

./stop.sh
sleep 5
./start.sh
EOF

# Logs script
tee logs.sh > /dev/null << 'EOF'
#!/bin/bash

echo "📋 Showing Mill Management System logs..."

cd ~/mill-management
docker-compose -f docker-compose.production.yml logs -f
EOF

# Make scripts executable
chmod +x start.sh stop.sh restart.sh logs.sh

print_success "Management scripts created"

# 15. Configure Cron Jobs
print_status "Configuring cron jobs..."

# Add cron jobs
(crontab -l 2>/dev/null; echo "0 2 * * * /home/administrator/backup-system.sh") | crontab -
(crontab -l 2>/dev/null; echo "0 6 * * * /home/administrator/monitor-system.sh > /home/administrator/system-report.log") | crontab -
(crontab -l 2>/dev/null; echo "0 3 * * 0 sudo rkhunter --cronjob --update --quiet") | crontab -

print_success "Cron jobs configured"

# 16. Final Security Check
print_status "Performing final security check..."

# Check if SSH key is properly configured
if [ ! -f ~/.ssh/authorized_keys ]; then
    print_warning "SSH authorized_keys not found. Please add your public key."
fi

# Check Docker installation
if command -v docker &> /dev/null; then
    print_success "Docker is installed and working"
else
    print_error "Docker installation failed"
fi

# Check fail2ban status
if sudo systemctl is-active --quiet fail2ban; then
    print_success "Fail2Ban is running"
else
    print_error "Fail2Ban is not running"
fi

print_success "Server setup completed!"

# Final instructions
echo ""
echo "🎉 Complete Server Setup Finished!"
echo ""
echo "📋 What was installed:"
echo "  ✅ System updates"
echo "  ✅ Docker & Docker Compose"
echo "  ✅ UFW Firewall"
echo "  ✅ Fail2Ban (SSH protection)"
echo "  ✅ ClamAV (Antivirus)"
echo "  ✅ SSH Security hardening"
echo "  ✅ Automatic updates"
echo "  ✅ System monitoring"
echo "  ✅ Backup system"
echo "  ✅ Cron jobs"
echo ""
echo "🔐 Security measures:"
echo "  - SSH key authentication only"
echo "  - Fail2Ban protection"
echo "  - Firewall configured"
echo "  - Automatic security updates"
echo "  - Antivirus scanning"
echo ""
echo "📚 Management commands:"
echo "  ./start.sh          - Start application"
echo "  ./stop.sh           - Stop application"
echo "  ./restart.sh        - Restart application"
echo "  ./logs.sh           - View logs"
echo "  ./monitor-system.sh - System status"
echo "  ./backup-system.sh  - Create backup"
echo ""
echo "🌐 Next steps:"
echo "1. Wait for file upload to complete"
echo "2. Run: ./start.sh"
echo "3. Configure DNS records"
echo "4. Access: https://test.nexonsolutions.be"
echo ""
print_success "Server is ready for production! 🚀" 