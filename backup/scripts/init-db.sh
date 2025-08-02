#!/bin/bash
set -e

echo "Starting database initialization..."

# Create databases
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE mill_db;
    CREATE DATABASE hardware_db;
EOSQL

# Create users
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER mill_user WITH PASSWORD 'mill_password_2024';
    CREATE USER hardware_user WITH PASSWORD 'hardware_password_2024';
EOSQL

# Grant privileges
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    GRANT ALL PRIVILEGES ON DATABASE mill_db TO mill_user;
    GRANT ALL PRIVILEGES ON DATABASE hardware_db TO hardware_user;
    ALTER USER mill_user CREATEDB;
    ALTER USER hardware_user CREATEDB;
EOSQL

# Set ownership
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    ALTER DATABASE mill_db OWNER TO mill_user;
    ALTER DATABASE hardware_db OWNER TO hardware_user;
EOSQL

# Enable extensions for mill_db
psql -v ON_ERROR_STOP=1 --username "mill_user" --dbname "mill_db" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO mill_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO mill_user;
EOSQL

# Enable extensions for hardware_db
psql -v ON_ERROR_STOP=1 --username "hardware_user" --dbname "hardware_db" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO hardware_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO hardware_user;
EOSQL

echo "Database initialization completed successfully!" 