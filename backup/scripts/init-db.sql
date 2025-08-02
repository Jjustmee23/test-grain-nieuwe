-- Initialize PostgreSQL databases and users
-- This script runs when the PostgreSQL container starts for the first time

-- Create the main database and user
CREATE DATABASE mill_db;
CREATE USER mill_user WITH PASSWORD 'mill_password_2024';
GRANT ALL PRIVILEGES ON DATABASE mill_db TO mill_user;
ALTER USER mill_user CREATEDB;

-- Create the hardware database and user
CREATE DATABASE hardware_db;
CREATE USER hardware_user WITH PASSWORD 'hardware_password_2024';
GRANT ALL PRIVILEGES ON DATABASE hardware_db TO hardware_user;
ALTER USER hardware_user CREATEDB;

-- Grant additional permissions
ALTER DATABASE mill_db OWNER TO mill_user;
ALTER DATABASE hardware_db OWNER TO hardware_user;

-- Enable extensions
\c mill_db;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

\c hardware_db;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set default privileges
\c mill_db;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO mill_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO mill_user;

\c hardware_db;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO hardware_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO hardware_user; 