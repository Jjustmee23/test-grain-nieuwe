#!/bin/bash

# Mill Management System - Production Deployment Script
# Ubuntu Server 24.04 LTS with Traefik

set -e

echo "🚀 Starting Mill Management System Deployment with Traefik..."
echo "📍 Target Server: 45.154.238.102"
echo "🌐 Domains: test.nexonsolutions.be, api.nexonsolutions.be, admin.nexonsolutions.be, monitor.nexonsolutions.be"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker
print_status "Installing Docker..."
if ! command -v docker &> /dev/null; then
    sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io
    sudo usermod -aG docker $USER
    print_success "Docker installed successfully"
else
    print_status "Docker already installed"
fi

# Install Docker Compose
print_status "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed successfully"
else
    print_status "Docker Compose already installed"
fi

# Create application directory
print_status "Setting up application directory..."
APP_DIR="/opt/mill-management"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copy application files
print_status "Copying application files..."
cp -r . $APP_DIR/
cd $APP_DIR

# Create logs directory
mkdir -p logs

# Set proper permissions
print_status "Setting file permissions..."
chmod +x deploy.sh
chmod +x start.sh
chmod +x stop.sh

# Create environment file
print_status "Creating environment configuration..."
cat > .env << EOF
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

# Create startup script
print_status "Creating startup script..."
cat > start.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting Mill Management System with Traefik..."

# Start all services
docker-compose -f docker-compose.production.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service status
echo "📊 Service Status:"
docker-compose -f docker-compose.production.yml ps

echo "✅ Mill Management System started successfully!"
echo "🌐 Access points:"
echo "  - Main App: https://test.nexonsolutions.be"
echo "  - API: https://api.nexonsolutions.be"
echo "  - Admin Panel: https://admin.nexonsolutions.be"
echo "  - Monitoring: https://monitor.nexonsolutions.be"
echo "  - Traefik Dashboard: https://traefik.nexonsolutions.be"
EOF

chmod +x start.sh

# Create stop script
print_status "Creating stop script..."
cat > stop.sh << 'EOF'
#!/bin/bash

echo "🛑 Stopping Mill Management System..."

# Stop all services
docker-compose -f docker-compose.production.yml down

echo "✅ Mill Management System stopped successfully!"
EOF

chmod +x stop.sh

# Create restart script
print_status "Creating restart script..."
cat > restart.sh << 'EOF'
#!/bin/bash

echo "🔄 Restarting Mill Management System..."

# Stop services
./stop.sh

# Wait a moment
sleep 5

# Start services
./start.sh
EOF

chmod +x restart.sh

# Create logs script
print_status "Creating logs script..."
cat > logs.sh << 'EOF'
#!/bin/bash

echo "📋 Showing Mill Management System logs..."

# Show logs for all services
docker-compose -f docker-compose.production.yml logs -f
EOF

chmod +x logs.sh

# Create backup script
print_status "Creating backup script..."
cat > backup.sh << 'EOF'
#!/bin/bash

echo "💾 Creating database backup..."

BACKUP_DIR="/opt/mill-backups"
mkdir -p $BACKUP_DIR

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/mill_backup_$TIMESTAMP.sql"

# Create database backup
docker-compose -f docker-compose.production.yml exec -T postgres pg_dump -U mill_user mill_management > $BACKUP_FILE

echo "✅ Backup created: $BACKUP_FILE"

# Keep only last 7 backups
cd $BACKUP_DIR
ls -t mill_backup_*.sql | tail -n +8 | xargs -r rm

echo "🧹 Cleaned up old backups (kept last 7)"
EOF

chmod +x backup.sh

# Create monitoring script
print_status "Creating monitoring script..."
cat > monitor.sh << 'EOF'
#!/bin/bash

echo "📊 Mill Management System Status:"

echo ""
echo "🐳 Docker Containers:"
docker-compose -f docker-compose.production.yml ps

echo ""
echo "🌐 Traefik Services:"
curl -s http://localhost:8080/api/http/services | jq '.[] | {name: .name, status: .status}' 2>/dev/null || echo "Traefik dashboard not accessible"

echo ""
echo "💾 Disk Usage:"
df -h

echo ""
echo "🧠 Memory Usage:"
free -h

echo ""
echo "🌐 Network Connections:"
netstat -tuln | grep -E ':(80|443|8080|5432|6379|5000|3000)'

echo ""
echo "📋 Recent Logs:"
docker-compose -f docker-compose.production.yml logs --tail=20
EOF

chmod +x monitor.sh

# Create SSL certificate script
print_status "Creating SSL certificate script..."
cat > setup-ssl.sh << 'EOF'
#!/bin/bash

echo "🔐 SSL certificates will be automatically managed by Traefik with Let's Encrypt"
echo "📋 Make sure your domains point to this server:"
echo "  - test.nexonsolutions.be"
echo "  - api.nexonsolutions.be"
echo "  - admin.nexonsolutions.be"
echo "  - monitor.nexonsolutions.be"
echo "  - traefik.nexonsolutions.be"

echo ""
echo "🚀 Starting services to get SSL certificates..."
./start.sh

echo ""
echo "⏳ Waiting for SSL certificates to be generated..."
sleep 60

echo "✅ SSL setup completed! Check Traefik dashboard for certificate status."
EOF

chmod +x setup-ssl.sh

# Create domain setup script
print_status "Creating domain setup script..."
cat > setup-domains.sh << 'EOF'
#!/bin/bash

echo "🌐 Domain Configuration Guide"
echo ""
echo "Configure your DNS records to point to this server (45.154.238.102):"
echo ""
echo "A Records:"
echo "  test.nexonsolutions.be     → 45.154.238.102"
echo "  api.nexonsolutions.be      → 45.154.238.102"
echo "  admin.nexonsolutions.be    → 45.154.238.102"
echo "  monitor.nexonsolutions.be  → 45.154.238.102"
echo "  traefik.nexonsolutions.be  → 45.154.238.102"
echo ""
echo "After configuring DNS, run: ./setup-ssl.sh"
EOF

chmod +x setup-domains.sh

print_success "Deployment scripts created successfully!"

# Final instructions
echo ""
echo "🎉 Traefik-based deployment setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Configure your domain DNS records (see setup-domains.sh)"
echo "2. Run: ./start.sh to start the application"
echo "3. Run: ./setup-ssl.sh to get SSL certificates"
echo "4. Access: https://test.nexonsolutions.be"
echo ""
echo "📚 Useful commands:"
echo "  ./start.sh         - Start all services"
echo "  ./stop.sh          - Stop all services"
echo "  ./restart.sh       - Restart all services"
echo "  ./logs.sh          - View logs"
echo "  ./monitor.sh       - System status"
echo "  ./backup.sh        - Database backup"
echo "  ./setup-domains.sh - Domain configuration guide"
echo ""
echo "🌐 Multi-domain setup:"
echo "  - Main App: https://test.nexonsolutions.be"
echo "  - API: https://api.nexonsolutions.be"
echo "  - Admin: https://admin.nexonsolutions.be"
echo "  - Monitoring: https://monitor.nexonsolutions.be"
echo "  - Traefik Dashboard: https://traefik.nexonsolutions.be"
echo ""
print_success "Mill Management System with Traefik is ready for deployment! 🚀" 