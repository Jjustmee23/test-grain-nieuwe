# 🏭 Mill Management System

Complete IoT-based mill management system with real-time monitoring, MQTT integration, and multi-domain support.

## 🚀 Quick Start

### Prerequisites
- Ubuntu Server 24.04 LTS
- Docker & Docker Compose
- Domain names pointing to your server

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/mill-management-system.git
cd mill-management-system
```

2. **Run the server setup:**
```bash
chmod +x server-setup.sh
./server-setup.sh
```

3. **Start the application:**
```bash
./start.sh
```

4. **Access the application:**
- Main App: https://test.nexonsolutions.be
- API: https://api.nexonsolutions.be
- Admin Panel: https://admin.nexonsolutions.be
- Monitoring: https://monitor.nexonsolutions.be
- Traefik Dashboard: https://traefik.nexonsolutions.be

## 🏗️ Architecture

```
Internet → Traefik (SSL) → Frontend/Backend → PostgreSQL
                    ↓
                MQTT Client → External Broker
```

## 📦 Services

- **🌐 Traefik** - Reverse proxy with automatic SSL
- **🐘 PostgreSQL** - Database for mill data
- **🔧 Node.js Backend** - API server
- **⚛️ React Frontend** - Web application
- **📡 MQTT Client** - IoT data collection
- **🔐 SSL Certificates** - Automatic Let's Encrypt
- **📊 Redis** - Caching layer

## 🔐 Security Features

- **Fail2Ban** - SSH protection
- **UFW Firewall** - Network security
- **ClamAV** - Antivirus scanning
- **SSH Key Authentication** - No password login
- **Automatic Updates** - Security patches
- **Rate Limiting** - DDoS protection

## 📡 MQTT Integration

Connects to external MQTT broker:
- **Broker**: 45.154.238.114
- **Username**: uc300
- **Password**: grain300
- **Topics**: device/+/power, device/+/status, etc.

## 🗄️ Database

- **Host**: postgres (Docker service)
- **Database**: mill_management
- **User**: mill_user
- **Password**: mill_password_2024

## 📚 Management Commands

```bash
./start.sh          # Start all services
./stop.sh           # Stop all services
./restart.sh        # Restart all services
./logs.sh           # View logs
./monitor-system.sh # System status
./backup-system.sh  # Create backup
```

## 🌐 Multi-Domain Setup

Configure DNS records pointing to your server:
- test.nexonsolutions.be → Main App
- api.nexonsolutions.be → Backend API
- admin.nexonsolutions.be → Admin Panel
- monitor.nexonsolutions.be → Monitoring
- traefik.nexonsolutions.be → Traefik Dashboard

## 🔧 Configuration

Environment variables in `.env`:
```bash
DB_HOST=postgres
DB_PORT=5432
DB_NAME=mill_management
DB_USER=mill_user
DB_PASSWORD=mill_password_2024
MQTT_BROKER=45.154.238.114
MQTT_USERNAME=uc300
MQTT_PASSWORD=grain300
```

## 📊 Features

- **Real-time Monitoring** - Live device status
- **Production Analytics** - Performance metrics
- **User Management** - Role-based access
- **Alert System** - Device notifications
- **Backup System** - Automatic backups
- **System Monitoring** - Health checks

## 🛠️ Development

### Backend
```bash
cd backend
npm install
npm run dev
```

### Frontend
```bash
cd frontend
npm install
npm start
```

### MQTT Client
```bash
cd mqtt-client
npm install
npm run dev
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Support

For support and questions, please open an issue on GitHub.

---

**Built with ❤️ for efficient mill management** 