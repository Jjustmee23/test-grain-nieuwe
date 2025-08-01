# Mill Management Application - React Edition

Modern React + Node.js version of the Mill Management Dashboard voor graanverwerkende fabrieken in Irak.

## 🏗️ Architecture

- **Frontend**: React 18 + TypeScript + Material-UI (MUI) v5
- **Backend**: Node.js + Express + TypeScript + Prisma ORM
- **Database**: PostgreSQL (existing database preserved)
- **Real-time**: WebSocket + MQTT integration
- **Authentication**: JWT + 2FA
- **State Management**: Redux Toolkit + RTK Query
- **Charts**: Recharts
- **Deployment**: Docker

## 📊 Features

### Core Modules
1. **Factory Management** - Beheer van molens in verschillende steden (Government/Private/Commercial)
2. **IoT Device Monitoring** - Real-time monitoring van sensoren en apparaten
3. **Batch Processing** - Productie batch beheer (wheat input → flour output)
4. **Power Management** - Energie monitoring en alerts
5. **Production Analytics** - Uitgebreide statistieken en charts
6. **User Management** - Multi-user systeem met verschillende rollen
7. **Real-time Data** - MQTT data ontvangst van IoT sensoren (elke 5 min)
8. **Notifications** - Email alerts via Microsoft365
9. **Support System** - Ticket management en feedback
10. **Security** - 2FA, role-based permissions

### Improvements over Django Version
- ⚡ **Modern UI**: Material-UI components with improved UX
- 🔄 **Real-time Updates**: WebSocket for instant data updates
- 📱 **Responsive Design**: Mobile-first approach
- 🚀 **Performance**: Optimized with React Query caching
- 🔒 **Security**: Modern JWT authentication with refresh tokens
- 📊 **Better Charts**: Interactive Recharts instead of Chart.js
- 🐳 **Docker**: Improved containerization

## 🗄️ Database

**Preserves existing PostgreSQL database - NO DATA LOSS!**

- **Main Database**: testdb (45.154.238.114:5433)
- **Hardware Database**: counter (45.154.238.114:5432)
- **33 Models**: All existing Django models replicated

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repo>
cd mill-react-application

# Start with Docker
docker-compose up --build

# Or development mode
cd backend && npm install && npm run dev
cd frontend && npm install && npm start
```

## 📁 Project Structure

```
mill-react-application/
├── frontend/           # React + TypeScript app
├── backend/           # Node.js + Express API
├── shared/           # Shared types/interfaces
├── docs/            # Documentation
├── docker-compose.yml
└── README.md
```

## 🌐 Access

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Docs**: http://localhost:5000/api-docs

---

**Migrated from Django with ❤️ - All data preserved!** 