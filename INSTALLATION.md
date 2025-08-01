# 🏭 Mill Management Application - Installation Guide

Modern React + Node.js version van het Mill Management Dashboard voor graanverwerkende fabrieken in Irak.

## 🎯 Overzicht

Deze applicatie is een volledige modernisering van de bestaande Django applicatie met:

- **Frontend**: React 18 + TypeScript + Material-UI v5
- **Backend**: Node.js + Express + TypeScript + Prisma ORM  
- **Database**: PostgreSQL (bestaande database behouden - **GEEN DATA VERLIES!**)
- **Real-time**: WebSocket + MQTT integration
- **Authentication**: JWT + 2FA
- **State Management**: Redux Toolkit + RTK Query
- **Charts**: Recharts (interactief)
- **Deployment**: Docker

## 📋 Vereisten

### Systeem Vereisten
- **Node.js**: 18.0.0 of hoger
- **npm**: 8.0.0 of hoger
- **Docker**: 20.10.0 of hoger (optioneel)
- **PostgreSQL**: 12+ (database al beschikbaar)

### Database Info
- **Main Database**: testdb op 45.154.238.114:5433 (testuser/testpassword)
- **Hardware Database**: counter op 45.154.238.114:5432 (root/testpassword)

## 🚀 Snelle Start

### Optie 1: Docker (Aanbevolen)

```bash
# 1. Clone de repository
git clone <your-repo-url>
cd mill-react-application

# 2. Kopieer environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. Update database credentials in .env files
# (Database credentials zijn al correct ingesteld)

# 4. Start de volledige stack
docker-compose up --build

# 5. Open de applicatie
# Frontend: http://localhost:3000
# Backend API: http://localhost:5000
# API Docs: http://localhost:5000/api-docs
```

### Optie 2: Lokale Development

```bash
# 1. Clone de repository
git clone <your-repo-url>
cd mill-react-application

# 2. Backend setup
cd backend
cp .env.example .env
npm install
npm run prisma:generate
npm run dev

# 3. Frontend setup (nieuwe terminal)
cd ../frontend
npm install
npm start

# 4. Redis (nieuwe terminal - optioneel voor development)
redis-server
```

## 🔧 Gedetailleerde Setup

### Backend Setup

```bash
cd backend

# Install dependencies
npm install

# Setup environment
cp .env.example .env

# Edit .env file met juiste database credentials:
DATABASE_URL="postgresql://testuser:testpassword@45.154.238.114:5433/testdb?schema=public"
COUNTER_DATABASE_URL="postgresql://root:testpassword@45.154.238.114:5432/counter?schema=public"
JWT_SECRET="your-super-secret-jwt-key"
JWT_REFRESH_SECRET="your-refresh-secret-key"

# Generate Prisma client
npm run prisma:generate

# Test database connection
npm run prisma:studio

# Start development server
npm run dev
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
echo "REACT_APP_API_URL=http://localhost:5000/api" > .env.local
echo "REACT_APP_WS_URL=ws://localhost:5000" >> .env.local

# Start development server
npm start
```

### Database Setup

De database is al geconfigureerd en bevat bestaande data. **Geen migraties nodig!**

```bash
# Test database connectie
cd backend
npm run prisma:studio

# Dit opent Prisma Studio waar je de data kunt bekijken:
# http://localhost:5555
```

## 🐳 Docker Configuratie

### Development met Docker

```bash
# Start alle services
docker-compose up --build

# Start alleen database services
docker-compose up redis

# Stop alle services
docker-compose down

# Rebuild na code changes
docker-compose up --build --force-recreate
```

### Production Deployment

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose logs -f
```

## 🌐 Service URLs

| Service | Development | Production | Docker |
|---------|-------------|------------|--------|
| Frontend | http://localhost:3000 | https://your-domain.com | http://localhost:3000 |
| Backend API | http://localhost:5000 | https://api.your-domain.com | http://localhost:5000 |
| API Docs | http://localhost:5000/api-docs | https://api.your-domain.com/api-docs | http://localhost:5000/api-docs |
| Prisma Studio | http://localhost:5555 | - | http://localhost:5555 |
| Redis | localhost:6379 | - | redis:6379 |

## 🔐 Authenticatie Setup

### JWT Configuration

```bash
# Generate secure JWT secrets
node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"

# Update .env file:
JWT_SECRET="generated-secret-key"
JWT_REFRESH_SECRET="another-generated-secret-key"
```

### 2FA Setup

2FA is automatisch beschikbaar voor alle gebruikers. Gebruikers kunnen het inschakelen in hun profiel.

## 📱 MQTT Integration

### MQTT Broker Setup

```bash
# Docker MQTT broker (optioneel)
docker run -it -p 1883:1883 -p 9001:9001 eclipse-mosquitto

# Update .env:
MQTT_BROKER_URL=mqtt://localhost:1883
MQTT_USERNAME=your-mqtt-username
MQTT_PASSWORD=your-mqtt-password
```

### Device Data Format

Devices sturen data naar MQTT topics:
```
mill/devices/{DEVICE_ID}/data
mill/devices/{DEVICE_ID}/status
mill/devices/{DEVICE_ID}/power
mill/devices/{DEVICE_ID}/door
```

## 📊 Features Overview

### ✅ Geïmplementeerde Features

1. **Factory Management** ✅
   - CRUD operaties voor molens
   - Locatie mapping (lat/lng)
   - Groepering (Government/Private/Commercial)
   - Multi-user access control

2. **IoT Device Monitoring** ✅
   - Real-time device data ontvangst
   - MQTT integration
   - Counter value tracking
   - Device status monitoring

3. **Batch Processing** ✅
   - Batch templates
   - Wheat → Flour conversion
   - Progress tracking
   - Batch approval workflow

4. **Power Management** ✅
   - Real-time power monitoring
   - Power loss/restore events
   - Email notifications
   - Power analytics dashboard

5. **Production Analytics** ✅
   - Interactive Recharts visualisaties
   - Daily/Weekly/Monthly/Yearly views
   - Factory comparison
   - Export capabilities

6. **User Management** ✅
   - JWT authentication
   - Role-based permissions
   - 2FA support
   - User profiles met factory access

7. **Real-time Updates** ✅
   - WebSocket integration
   - Live device data
   - Instant notifications
   - Real-time charts

8. **Notifications** ✅
   - In-app notifications
   - Email integration via Microsoft365
   - Notification preferences
   - System alerts

9. **Support System** ✅
   - Ticket management
   - User feedback
   - Internal notes
   - Status tracking

10. **Security** ✅
    - JWT + Refresh tokens
    - 2FA support
    - Rate limiting
    - Input validation

### 🔄 Real-time Features

- **Device Data**: Live MQTT data elke 5 minuten
- **Production Updates**: Real-time counter updates
- **Power Events**: Instant power loss/restore notifications
- **Batch Progress**: Live batch status updates
- **System Alerts**: Real-time system notifications

## 🎨 UI Improvements

### Material-UI v5 Features
- **Modern Design**: Clean, professional interface
- **Dark/Light Theme**: User preference support
- **Responsive**: Mobile-first design
- **Arabic Support**: RTL layout support
- **Accessibility**: WCAG 2.1 compliant

### Interactive Charts
- **Recharts**: Modern, interactive visualisaties
- **Real-time Updates**: Live data updates
- **Export Options**: PNG, SVG, PDF export
- **Zoom & Pan**: Advanced chart interactions

## 🔧 Development

### Backend Development

```bash
cd backend

# Watch mode
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint
npm run lint:fix

# Testing
npm test
npm run test:watch

# Database
npm run prisma:studio
npm run prisma:generate
```

### Frontend Development

```bash
cd frontend

# Development server
npm start

# Type checking
npm run type-check

# Linting & Formatting
npm run lint
npm run lint:fix
npm run format

# Testing
npm test
npm run test:coverage

# Build
npm run build
npm run analyze
```

## 📦 Production Deployment

### Ubuntu Server Setup

```bash
# 1. Install Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 2. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Setup application
git clone <your-repo>
cd mill-react-application
cp .env.example .env

# 4. Update production environment variables
# Edit .env with production settings

# 5. Deploy
docker-compose -f docker-compose.prod.yml up -d

# 6. Setup SSL (with Nginx proxy)
# Install certbot and configure SSL certificates
```

### Environment Variables (Production)

```bash
# .env (production)
NODE_ENV=production
JWT_SECRET=<64-char-hex-secret>
JWT_REFRESH_SECRET=<64-char-hex-secret>

# Database (unchanged)
DATABASE_URL="postgresql://testuser:testpassword@45.154.238.114:5433/testdb?schema=public"
COUNTER_DATABASE_URL="postgresql://root:testpassword@45.154.238.114:5432/counter?schema=public"

# Redis
REDIS_URL=redis://redis:6379

# MQTT
MQTT_BROKER_URL=mqtt://your-production-mqtt-broker:1883

# Microsoft 365
MS365_CLIENT_ID=your-production-client-id
MS365_CLIENT_SECRET=your-production-client-secret
MS365_TENANT_ID=your-tenant-id
```

## 🐛 Troubleshooting

### Veel Voorkomende Problemen

1. **Database Connection Error**
   ```bash
   # Check database connectivity
   cd backend
   npm run prisma:studio
   ```

2. **Redis Connection Error**
   ```bash
   # Start Redis
   redis-server
   # or with Docker
   docker run -d -p 6379:6379 redis:alpine
   ```

3. **MQTT Connection Error**
   ```bash
   # Check MQTT broker
   mosquitto_pub -h localhost -t test -m "hello"
   ```

4. **Frontend Build Errors**
   ```bash
   # Clear cache and reinstall
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

5. **Permission Errors**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   chmod -R 755 .
   ```

### Database Issues

```bash
# Reset Prisma client
cd backend
rm -rf node_modules/.prisma
npm run prisma:generate

# Check database schema
npm run prisma:studio

# Manual database connection test
psql -h 45.154.238.114 -p 5433 -U testuser -d testdb
```

### Docker Issues

```bash
# Clean Docker cache
docker system prune -a

# Rebuild with no cache
docker-compose build --no-cache

# Check container logs
docker-compose logs backend
docker-compose logs frontend
```

## 📚 API Documentation

Na het starten van de backend is de API documentatie beschikbaar op:
- **Development**: http://localhost:5000/api-docs
- **Production**: https://your-domain.com/api-docs

### Belangrijke Endpoints

```
# Authentication
POST /api/auth/login
POST /api/auth/refresh
POST /api/auth/logout

# Factories
GET /api/factories
POST /api/factories
GET /api/factories/:id
PUT /api/factories/:id
DELETE /api/factories/:id

# Devices
GET /api/devices
POST /api/devices
GET /api/devices/:id
PUT /api/devices/:id

# Batches
GET /api/batches
POST /api/batches
GET /api/batches/:id
PUT /api/batches/:id

# Power Management
GET /api/power/events
GET /api/power/status
POST /api/power/events/:id/resolve

# Analytics
GET /api/analytics/dashboard
GET /api/analytics/production
GET /api/analytics/factories
```

## 🎯 Volgende Stappen

1. **Start de applicatie** met Docker of lokaal
2. **Login** met bestaande Django gebruikers
3. **Verken** de nieuwe features
4. **Configureer** MQTT broker voor real-time data
5. **Setup** Microsoft365 voor email notifications
6. **Deploy** naar productie server

## 💡 Tips

- **Development**: Gebruik `npm run dev` voor hot reload
- **Debugging**: Prisma Studio voor database inspectie
- **Performance**: Redis voor caching en sessies
- **Monitoring**: Check Docker logs voor issues
- **Backup**: Database is extern gehost en automatisch gebackupt

---

**🎉 Succes met je nieuwe moderne Mill Management applicatie!** 

Voor vragen of support, check de logs of open een issue in de repository. 