# 🚀 Mill Management System - Production Deployment Guide

## 📋 Overview

This guide will help you deploy the Mill Management System on your Ubuntu Server 24.04 LTS at `45.154.238.102` with domain `test.nexonsolutions.be`.

## 🎯 What We're Deploying

- **🌐 Nginx** - Reverse proxy with SSL
- **🐘 PostgreSQL** - Database for mill data
- **🔧 Node.js Backend** - API server
- **⚛️ React Frontend** - Web application
- **📡 MQTT Client** - IoT data collection
- **🔐 SSL Certificate** - Secure HTTPS
- **📊 Redis** - Caching layer

## 🏗️ Architecture

```
Internet → Nginx (SSL) → Frontend/Backend → PostgreSQL
                    ↓
                MQTT Client → 45.154.238.114 (Broker)
```

## 📦 Prerequisites

- Ubuntu Server 24.04 LTS at `45.154.238.102`
- Domain `test.nexonsolutions.be` pointing to the server
- SSH access to the server
- MQTT Broker at `45.154.238.114`

## 🚀 Quick Deployment

### Step 1: Connect to Server
```bash
ssh root@45.154.238.102
```

### Step 2: Run Deployment Script
```bash
# Upload files to server (from your local machine)
scp -r . root@45.154.238.102:/opt/mill-management

# On the server
cd /opt/mill-management
chmod +x deploy.sh
./deploy.sh
```

### Step 3: Start Services
```bash
./start.sh
```

### Step 4: Setup SSL
```bash
./setup-ssl.sh
```

### Step 5: Access Application
Open your browser and go to: `https://test.nexonsolutions.be`

## 📁 File Structure

```
/opt/mill-management/
├── docker-compose.production.yml  # Main deployment config
├── backend/                       # Node.js API
├── frontend/                      # React app
├── mqtt-client/                   # IoT data collector
├── nginx/                         # Web server config
├── deploy.sh                      # Deployment script
├── start.sh                       # Start services
├── stop.sh                        # Stop services
├── restart.sh                     # Restart services
├── logs.sh                        # View logs
├── monitor.sh                     # System status
├── backup.sh                      # Database backup
└── setup-ssl.sh                   # SSL certificate
```

## 🔧 Configuration

### Environment Variables
The system uses these environment variables:

```bash
# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=mill_management
DB_USER=mill_user
DB_PASSWORD=mill_password_2024

# MQTT Broker
MQTT_BROKER=45.154.238.114
MQTT_USERNAME=uc300
MQTT_PASSWORD=grain300
MQTT_PORT=1883

# Security
JWT_SECRET=mill_jwt_secret_2024_production
CORS_ORIGIN=https://test.nexonsolutions.be
```

### Database Schema
The system creates these tables automatically:

- `device_power_status` - Device power and temperature data
- `door_status` - Device door open/close status
- `production_data` - Daily production counts

## 📊 Management Commands

### Start Services
```bash
./start.sh
```

### Stop Services
```bash
./stop.sh
```

### Restart Services
```bash
./restart.sh
```

### View Logs
```bash
./logs.sh
```

### System Status
```bash
./monitor.sh
```

### Database Backup
```bash
./backup.sh
```

### SSL Certificate
```bash
./setup-ssl.sh
```

## 🔍 Monitoring

### Check Service Status
```bash
docker-compose -f docker-compose.production.yml ps
```

### View Container Logs
```bash
# All services
docker-compose -f docker-compose.production.yml logs

# Specific service
docker-compose -f docker-compose.production.yml logs backend
docker-compose -f docker-compose.production.yml logs frontend
docker-compose -f docker-compose.production.yml logs mqtt-client
```

### System Resources
```bash
# Disk usage
df -h

# Memory usage
free -h

# Network connections
netstat -tuln
```

## 🔐 Security

### SSL Certificate
- Automatically obtained via Let's Encrypt
- Auto-renewal configured
- HTTPS enforced

### Firewall
```bash
# Open required ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

### Database Security
- Non-root user for database access
- Strong passwords
- Network isolation via Docker

## 📡 MQTT Integration

The MQTT client automatically:

1. **Connects** to broker at `45.154.238.114`
2. **Subscribes** to topics:
   - `device/+/power`
   - `device/+/status`
   - `device/+/door`
   - `device/+/production`
   - `uc300/+/+`
   - `grain/+/+`
   - `mill/+/+`

3. **Decodes** payloads and stores in PostgreSQL
4. **Handles** reconnections automatically

## 🗄️ Database

### Connection Details
- **Host**: `postgres` (Docker service)
- **Port**: `5432`
- **Database**: `mill_management`
- **User**: `mill_user`
- **Password**: `mill_password_2024`

### Backup
```bash
# Manual backup
./backup.sh

# Automatic daily backup (add to crontab)
0 2 * * * /opt/mill-management/backup.sh
```

## 🐛 Troubleshooting

### Services Not Starting
```bash
# Check Docker status
sudo systemctl status docker

# Check container logs
docker-compose -f docker-compose.production.yml logs

# Restart Docker
sudo systemctl restart docker
```

### SSL Certificate Issues
```bash
# Check certificate status
docker-compose -f docker-compose.production.yml run --rm certbot certificates

# Renew certificate
docker-compose -f docker-compose.production.yml run --rm certbot renew
```

### Database Connection Issues
```bash
# Check database container
docker-compose -f docker-compose.production.yml exec postgres psql -U mill_user -d mill_management

# Check database logs
docker-compose -f docker-compose.production.yml logs postgres
```

### MQTT Connection Issues
```bash
# Check MQTT client logs
docker-compose -f docker-compose.production.yml logs mqtt-client

# Test MQTT connection
docker-compose -f docker-compose.production.yml exec mqtt-client node -e "
const mqtt = require('mqtt');
const client = mqtt.connect('mqtt://45.154.238.114:1883', {
  username: 'uc300',
  password: 'grain300'
});
client.on('connect', () => console.log('Connected'));
client.on('error', (err) => console.error(err));
"
```

## 🔄 Updates

### Update Application
```bash
# Stop services
./stop.sh

# Pull latest code
git pull origin main

# Rebuild and start
docker-compose -f docker-compose.production.yml build
./start.sh
```

### Update SSL Certificate
```bash
./setup-ssl.sh
```

## 📞 Support

If you encounter issues:

1. Check the logs: `./logs.sh`
2. Check system status: `./monitor.sh`
3. Restart services: `./restart.sh`
4. Check Docker containers: `docker ps`

## 🎉 Success!

Once deployed, you can:

- **Access the web interface** at `https://test.nexonsolutions.be`
- **Monitor real-time data** from your mills
- **View device status** and production data
- **Receive alerts** for device issues
- **Generate reports** and analytics

The system will automatically collect data from your MQTT broker and provide a comprehensive mill management interface! 🏭✨ 