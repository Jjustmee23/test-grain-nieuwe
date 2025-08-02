#!/bin/bash

# Mill Management System Production Deployment Script
# Complete setup with persistent volumes, monitoring, and backup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_NAME="mill-management"
DATA_DIR="/opt/mill"
BACKUP_DIR="/opt/mill/backups"
LOG_DIR="/opt/mill/logs"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root"
        exit 1
    fi
}

# Install required packages
install_packages() {
    log "Installing required packages..."
    
    sudo apt-get update
    sudo apt-get install -y \
        curl \
        wget \
        git \
        htop \
        iotop \
        nethogs \
        tree \
        unzip \
        jq \
        awscli \
        postgresql-client \
        redis-tools
}

# Create directory structure
create_directories() {
    log "Creating directory structure..."
    
    # Create main data directory
    sudo mkdir -p "$DATA_DIR"
    sudo chown $USER:$USER "$DATA_DIR"
    
    # Create subdirectories
    local dirs=(
        "$DATA_DIR/postgres/data"
        "$DATA_DIR/postgres/backups"
        "$DATA_DIR/redis/data"
        "$DATA_DIR/grafana/data"
        "$DATA_DIR/grafana/provisioning"
        "$DATA_DIR/prometheus/data"
        "$DATA_DIR/traefik/certs"
        "$DATA_DIR/traefik/logs"
        "$DATA_DIR/backend/logs"
        "$DATA_DIR/frontend/logs"
        "$DATA_DIR/mqtt/logs"
        "$BACKUP_DIR"
        "$LOG_DIR"
    )
    
    for dir in "${dirs[@]}"; do
        sudo mkdir -p "$dir"
        sudo chown $USER:$USER "$dir"
        sudo chmod 755 "$dir"
    done
    
    log "Directory structure created"
}

# Setup PostgreSQL configuration
setup_postgres() {
    log "Setting up PostgreSQL configuration..."
    
    # Create PostgreSQL config directory
    mkdir -p postgres/conf
    mkdir -p postgres/init
    
    # PostgreSQL configuration for high performance
    cat > postgres/conf/postgresql.conf << 'EOF'
# PostgreSQL Configuration for Mill Management System
# Optimized for high throughput and reliability

# Connection settings
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_temp_files = -1
log_autovacuum_min_duration = 0
log_error_verbosity = verbose

# Query tuning
random_page_cost = 1.1
effective_io_concurrency = 200

# Autovacuum
autovacuum = on
autovacuum_max_workers = 3
autovacuum_naptime = 1min
autovacuum_vacuum_threshold = 50
autovacuum_analyze_threshold = 50

# WAL settings
wal_level = replica
max_wal_size = 1GB
min_wal_size = 80MB

# Replication
max_replication_slots = 5
max_wal_senders = 5

# Performance
work_mem = 4MB
temp_buffers = 16MB
EOF

    # Create initialization script
    cat > postgres/init/01-init.sql << 'EOF'
-- Mill Management System Database Initialization

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create additional databases if needed
-- CREATE DATABASE mill_analytics;
-- CREATE DATABASE mill_archive;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE mill_management TO mill_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mill_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mill_user;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_uc300_official_device_timestamp 
ON uc300_official_data(device_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_uc300_official_data_type_timestamp 
ON uc300_official_data(data_type, timestamp DESC);

-- Create materialized view for device statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS device_stats AS
SELECT 
    device_id,
    COUNT(*) as message_count,
    MAX(timestamp) as last_seen,
    AVG(signal_strength) as avg_signal,
    MAX(di2_counter) as max_counter
FROM uc300_official_data 
GROUP BY device_id;

-- Create refresh function
CREATE OR REPLACE FUNCTION refresh_device_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW device_stats;
END;
$$ LANGUAGE plpgsql;

-- Create scheduled job (requires pg_cron extension)
-- SELECT cron.schedule('refresh-device-stats', '*/5 * * * *', 'SELECT refresh_device_stats();');
EOF

    log "PostgreSQL configuration created"
}

# Setup Grafana dashboards
setup_grafana() {
    log "Setting up Grafana configuration..."
    
    # Create Grafana provisioning directory
    mkdir -p grafana/provisioning/datasources
    mkdir -p grafana/provisioning/dashboards
    mkdir -p grafana/dashboards
    
    # Copy datasource configuration
    cp grafana/datasources/postgres.yml grafana/provisioning/datasources/
    
    # Create dashboard provisioning
    cat > grafana/provisioning/dashboards/dashboard.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

    log "Grafana configuration created"
}

# Setup Prometheus configuration
setup_prometheus() {
    log "Setting up Prometheus configuration..."
    
    mkdir -p prometheus/rules
    
    # Create alerting rules
    cat > prometheus/rules/alerts.yml << 'EOF'
groups:
  - name: mill-management
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is above 80% for more than 5 minutes"

      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is above 80% for more than 5 minutes"

      - alert: HighDiskUsage
        expr: (1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High disk usage on {{ $labels.instance }}"
          description: "Disk usage is above 80% for more than 5 minutes"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database is down"
          description: "PostgreSQL database is not responding"

      - alert: MQTTClientDown
        expr: up{job="mqtt-client"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "MQTT client is down"
          description: "MQTT client is not running"

      - alert: BackendDown
        expr: up{job="backend"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Backend API is down"
          description: "Backend API is not responding"
EOF

    log "Prometheus configuration created"
}

# Setup backup cron job
setup_backup_cron() {
    log "Setting up backup cron job..."
    
    # Create backup script
    cat > backup-cron.sh << 'EOF'
#!/bin/bash
cd /opt/mill
docker-compose -f docker-compose.production.yml exec -T backup /scripts/backup.sh backup
EOF

    chmod +x backup-cron.sh
    
    # Add to crontab (daily at 2 AM)
    (crontab -l 2>/dev/null; echo "0 2 * * * /opt/mill/backup-cron.sh >> /opt/mill/logs/backup.log 2>&1") | crontab -
    
    log "Backup cron job configured"
}

# Setup monitoring scripts
setup_monitoring() {
    log "Setting up monitoring scripts..."
    
    # Create health check script
    cat > health-check.sh << 'EOF'
#!/bin/bash

# Health check script for Mill Management System

LOG_FILE="/opt/mill/logs/health.log"
ALERT_EMAIL="admin@nexonsolutions.be"

# Check Docker containers
check_containers() {
    local containers=(
        "mill_postgres"
        "mill_redis"
        "mill_backend"
        "mill_frontend"
        "mill_mqtt_client"
        "mill_grafana"
        "mill_prometheus"
        "mill_traefik"
    )
    
    for container in "${containers[@]}"; do
        if ! docker ps --format "table {{.Names}}" | grep -q "$container"; then
            echo "[$(date)] ERROR: Container $container is not running" >> "$LOG_FILE"
            return 1
        fi
    done
    
    echo "[$(date)] INFO: All containers are running" >> "$LOG_FILE"
    return 0
}

# Check database connectivity
check_database() {
    if ! docker exec mill_postgres pg_isready -U mill_user -d mill_management > /dev/null 2>&1; then
        echo "[$(date)] ERROR: Database is not accessible" >> "$LOG_FILE"
        return 1
    fi
    
    echo "[$(date)] INFO: Database is accessible" >> "$LOG_FILE"
    return 0
}

# Check MQTT connection
check_mqtt() {
    # This would require a more sophisticated check
    echo "[$(date)] INFO: MQTT check skipped (requires external broker)" >> "$LOG_FILE"
    return 0
}

# Main health check
main() {
    local failed=0
    
    check_containers || failed=1
    check_database || failed=1
    check_mqtt || failed=1
    
    if [ $failed -eq 1 ]; then
        echo "[$(date)] ERROR: Health check failed" >> "$LOG_FILE"
        # Send alert email
        echo "Mill Management System health check failed. Check logs at $LOG_FILE" | \
        mail -s "Mill System Alert" "$ALERT_EMAIL" 2>/dev/null || true
    else
        echo "[$(date)] INFO: Health check passed" >> "$LOG_FILE"
    fi
}

main
EOF

    chmod +x health-check.sh
    
    # Add health check to crontab (every 5 minutes)
    (crontab -l 2>/dev/null; echo "*/5 * * * * /opt/mill/health-check.sh") | crontab -
    
    log "Monitoring scripts created"
}

# Setup log rotation
setup_log_rotation() {
    log "Setting up log rotation..."
    
    # Create logrotate configuration
    sudo tee /etc/logrotate.d/mill-management > /dev/null << 'EOF'
/opt/mill/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        docker-compose -f /opt/mill/docker-compose.production.yml restart backend mqtt-client
    endscript
}

/opt/mill/traefik/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        docker-compose -f /opt/mill/docker-compose.production.yml restart traefik
    endscript
}
EOF

    log "Log rotation configured"
}

# Build and start services
deploy_services() {
    log "Building and starting services..."
    
    # Build all services
    docker-compose -f docker-compose.production.yml build
    
    # Start services
    docker-compose -f docker-compose.production.yml up -d
    
    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    sleep 30
    
    # Check service status
    docker-compose -f docker-compose.production.yml ps
    
    log "Services deployed successfully"
}

# Setup firewall
setup_firewall() {
    log "Setting up firewall..."
    
    # Allow required ports
    sudo ufw allow 22/tcp    # SSH
    sudo ufw allow 80/tcp    # HTTP
    sudo ufw allow 443/tcp   # HTTPS
    sudo ufw allow 8080/tcp  # Traefik dashboard
    
    # Enable firewall
    sudo ufw --force enable
    
    log "Firewall configured"
}

# Create management scripts
create_management_scripts() {
    log "Creating management scripts..."
    
    # Start script
    cat > start.sh << 'EOF'
#!/bin/bash
cd /opt/mill
docker-compose -f docker-compose.production.yml up -d
echo "Mill Management System started"
EOF

    # Stop script
    cat > stop.sh << 'EOF'
#!/bin/bash
cd /opt/mill
docker-compose -f docker-compose.production.yml down
echo "Mill Management System stopped"
EOF

    # Restart script
    cat > restart.sh << 'EOF'
#!/bin/bash
cd /opt/mill
docker-compose -f docker-compose.production.yml restart
echo "Mill Management System restarted"
EOF

    # Logs script
    cat > logs.sh << 'EOF'
#!/bin/bash
cd /opt/mill
docker-compose -f docker-compose.production.yml logs -f "$@"
EOF

    # Backup script
    cat > backup.sh << 'EOF'
#!/bin/bash
cd /opt/mill
docker-compose -f docker-compose.production.yml exec backup /scripts/backup.sh "$@"
EOF

    # Status script
    cat > status.sh << 'EOF'
#!/bin/bash
cd /opt/mill
echo "=== Mill Management System Status ==="
docker-compose -f docker-compose.production.yml ps
echo ""
echo "=== Resource Usage ==="
docker stats --no-stream
echo ""
echo "=== Recent Logs ==="
docker-compose -f docker-compose.production.yml logs --tail=10
EOF

    # Make scripts executable
    chmod +x start.sh stop.sh restart.sh logs.sh backup.sh status.sh
    
    log "Management scripts created"
}

# Main deployment function
main() {
    log "Starting Mill Management System production deployment..."
    
    # Check prerequisites
    check_root
    
    # Install packages
    install_packages
    
    # Create directories
    create_directories
    
    # Setup configurations
    setup_postgres
    setup_grafana
    setup_prometheus
    
    # Setup monitoring and backup
    setup_backup_cron
    setup_monitoring
    setup_log_rotation
    
    # Setup firewall
    setup_firewall
    
    # Deploy services
    deploy_services
    
    # Create management scripts
    create_management_scripts
    
    log "Deployment completed successfully!"
    log ""
    log "=== Access Information ==="
    log "Frontend: https://test.nexonsolutions.be"
    log "API: https://api.nexonsolutions.be"
    log "Grafana: https://grafana.nexonsolutions.be (admin/mill_grafana_2024)"
    log "Prometheus: https://prometheus.nexonsolutions.be"
    log "Traefik Dashboard: http://localhost:8080"
    log ""
    log "=== Management Commands ==="
    log "./start.sh    - Start all services"
    log "./stop.sh     - Stop all services"
    log "./restart.sh  - Restart all services"
    log "./logs.sh     - View logs"
    log "./backup.sh   - Create backup"
    log "./status.sh   - System status"
    log ""
    log "=== Backup Information ==="
    log "Local backups: $BACKUP_DIR"
    log "S3 bucket: $S3_BUCKET (if configured)"
    log "Retention: $RETENTION_DAYS days"
    log ""
    log "=== Monitoring ==="
    log "Health checks: Every 5 minutes"
    log "Backup schedule: Daily at 2 AM"
    log "Log rotation: Daily, 30 days retention"
}

# Run main function
main "$@" 