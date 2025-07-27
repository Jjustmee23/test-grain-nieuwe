# Database Setup Guide

## 🗄️ PostgreSQL Database Configuration

### Database Details
- **Host**: 45.154.238.114
- **Port**: 5432
- **Database**: counter
- **User**: root
- **Password**: testpassword

### ⚠️ Important: Database Structure Protection

**NO DATABASE STRUCTURE CHANGES ARE ALLOWED**

The application is configured to:
- ✅ **Allow**: Adding/removing data (cities, factories, devices, etc.)
- ✅ **Allow**: Reading existing data
- ✅ **Allow**: Updating existing records
- ❌ **Block**: Creating new tables
- ❌ **Block**: Modifying table structures
- ❌ **Block**: Running migrationss

## 🚀 How to Start the Application

### Option 1: Using Docker (Recommended)
```bash
# Build and start the application
docker-compose up --build

# The application will be available at: http://localhost:8000
```

### Option 2: Direct Python
```bash
# Install dependencies
pip install -r requirements.txt

# Check database connectivity (without changes)
python manage.py check_db

# Start the application
python manage.py runserver 0.0.0.0:8000
```

## 🔍 Database Connectivity Check

Before starting the application, you can check if the database is accessible:

```bash
# Check database connection and existing tables
python manage.py check_db
```

This command will:
- ✅ Test PostgreSQL connection
- ✅ List existing tables
- ✅ Check if mill tables exist
- ✅ Test Django model access
- ❌ **No structural changes made**

## 📊 Expected Database Tables

The application expects these tables to exist:
- `mill_city` - Cities where mills are located
- `mill_factory` - Individual mill facilities
- `mill_device` - IoT devices/sensors
- `mill_batch` - Production batches
- `mill_productiondata` - Production metrics
- `mill_transactiondata` - Real-time transaction data
- `mill_rawdata` - Detailed sensor data
- `mill_alert` - System alerts
- `mill_notification` - User notifications
- `mill_contactticket` - Support tickets
- `mill_feedback` - User feedback
- `auth_user` - User accounts
- `django_migrations` - Migration history (read-only)

## 🛡️ Safety Measures

The application includes several safety measures:

1. **Migration Disabled**: `MIGRATION_MODULES = {'mill': None}`
2. **Environment Variable**: `DJANGO_DISABLE_MIGRATIONS = True`
3. **Docker Environment**: `ENV DJANGO_DISABLE_MIGRATIONS True`
4. **Management Commands**: Blocked migration commands

## 🔧 Troubleshooting

### Database Connection Issues
```bash
# Test PostgreSQL connection directly
psql -h 45.154.238.114 -p 5432 -U root -d counter
```

### Application Won't Start
1. Check if database is accessible
2. Verify credentials are correct
3. Ensure no migration commands are being run

### Data Access Issues
- Ensure tables exist in the database
- Check if Django models can access the data
- Verify user permissions on the database

## 📝 Usage Notes

- **Data Management**: You can add/remove cities, factories, devices through the web interface
- **No Schema Changes**: The database structure is preserved exactly as-is
- **Read-Only Operations**: All database structure operations are blocked
- **Safe Operations**: Only data CRUD operations are allowed

## 🎯 Quick Start

1. **Check Database**: `python manage.py check_db`
2. **Start Application**: `docker-compose up --build`
3. **Access Web Interface**: http://localhost:8000
4. **Login**: Use existing user credentials
5. **Manage Data**: Add/remove cities, factories, devices through the web interface

The application is now ready to use with your existing PostgreSQL database structure! 