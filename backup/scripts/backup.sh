#!/bin/bash

# Mill Management System Backup Script
# Supports local and S3 backups

set -e

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
SCHEDULE=${BACKUP_SCHEDULE:-"0 2 * * *"}
S3_BUCKET=${S3_BUCKET:-"mill-backups"}
S3_ENDPOINT=${S3_ENDPOINT:-"s3.amazonaws.com"}
S3_ACCESS_KEY=${S3_ACCESS_KEY}
S3_SECRET_KEY=${S3_SECRET_KEY}

# Database configuration
DB_HOST="postgres"
DB_PORT="5432"
DB_NAME="mill_management"
DB_USER="mill_user"
DB_PASSWORD="mill_password_2024"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Function to create database backup
create_backup() {
    local timestamp=$(date +'%Y%m%d_%H%M%S')
    local backup_file="mill_backup_${timestamp}.sql"
    local backup_path="$BACKUP_DIR/$backup_file"
    local compressed_file="${backup_path}.gz"
    
    log "Starting database backup..."
    
    # Create PostgreSQL backup
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        --clean \
        --create \
        --if-exists \
        --no-owner \
        --no-privileges \
        > "$backup_path"
    
    if [ $? -eq 0 ]; then
        log "Database backup created: $backup_path"
        
        # Compress backup
        gzip "$backup_path"
        log "Backup compressed: $compressed_file"
        
        # Create backup metadata
        local metadata_file="${compressed_file}.meta"
        cat > "$metadata_file" << EOF
Backup created: $(date)
Database: $DB_NAME
Host: $DB_HOST
Size: $(du -h "$compressed_file" | cut -f1)
Checksum: $(sha256sum "$compressed_file" | cut -d' ' -f1)
EOF
        log "Backup metadata created: $metadata_file"
        
        return 0
    else
        error "Database backup failed"
        return 1
    fi
}

# Function to upload to S3
upload_to_s3() {
    local file_path="$1"
    local file_name=$(basename "$file_path")
    
    if [ -z "$S3_ACCESS_KEY" ] || [ -z "$S3_SECRET_KEY" ]; then
        warn "S3 credentials not configured, skipping S3 upload"
        return 0
    fi
    
    log "Uploading $file_name to S3..."
    
    # Use AWS CLI or curl for S3 upload
    if command -v aws &> /dev/null; then
        aws s3 cp "$file_path" "s3://$S3_BUCKET/$file_name" \
            --endpoint-url "https://$S3_ENDPOINT" \
            --quiet
    else
        # Fallback to curl (requires curl with S3 support)
        curl -X PUT \
            -T "$file_path" \
            -H "Host: $S3_BUCKET.$S3_ENDPOINT" \
            -H "Authorization: AWS4-HMAC-SHA256 Credential=$S3_ACCESS_KEY" \
            "https://$S3_BUCKET.$S3_ENDPOINT/$file_name"
    fi
    
    if [ $? -eq 0 ]; then
        log "Successfully uploaded $file_name to S3"
    else
        error "Failed to upload $file_name to S3"
        return 1
    fi
}

# Function to clean old backups
cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days..."
    
    # Clean local backups
    find "$BACKUP_DIR" -name "mill_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "mill_backup_*.sql.gz.meta" -mtime +$RETENTION_DAYS -delete
    
    # Clean S3 backups if configured
    if [ -n "$S3_ACCESS_KEY" ] && [ -n "$S3_SECRET_KEY" ]; then
        if command -v aws &> /dev/null; then
            aws s3 ls "s3://$S3_BUCKET/" | \
            awk '{print $4}' | \
            grep "mill_backup_.*\.sql\.gz$" | \
            while read file; do
                # Check if file is older than retention period
                file_date=$(aws s3 ls "s3://$S3_BUCKET/$file" | awk '{print $1, $2}')
                file_timestamp=$(date -d "$file_date" +%s)
                current_timestamp=$(date +%s)
                days_old=$(( (current_timestamp - file_timestamp) / 86400 ))
                
                if [ $days_old -gt $RETENTION_DAYS ]; then
                    aws s3 rm "s3://$S3_BUCKET/$file" --quiet
                    aws s3 rm "s3://$S3_BUCKET/$file.meta" --quiet 2>/dev/null || true
                    log "Deleted old S3 backup: $file"
                fi
            done
        fi
    fi
    
    log "Cleanup completed"
}

# Function to list backups
list_backups() {
    log "Local backups:"
    ls -la "$BACKUP_DIR"/mill_backup_*.sql.gz 2>/dev/null || echo "No local backups found"
    
    if [ -n "$S3_ACCESS_KEY" ] && [ -n "$S3_SECRET_KEY" ]; then
        log "S3 backups:"
        if command -v aws &> /dev/null; then
            aws s3 ls "s3://$S3_BUCKET/" | grep "mill_backup_.*\.sql\.gz$" || echo "No S3 backups found"
        fi
    fi
}

# Function to restore backup
restore_backup() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        error "No backup file specified"
        echo "Usage: $0 restore <backup_file>"
        exit 1
    fi
    
    log "Restoring from backup: $backup_file"
    
    # Check if file exists locally
    if [ ! -f "$backup_file" ]; then
        # Try to download from S3
        if [ -n "$S3_ACCESS_KEY" ] && [ -n "$S3_SECRET_KEY" ]; then
            log "Downloading backup from S3..."
            aws s3 cp "s3://$S3_BUCKET/$backup_file" "$BACKUP_DIR/" --quiet
            backup_file="$BACKUP_DIR/$backup_file"
        fi
    fi
    
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
        exit 1
    fi
    
    # Restore database
    log "Restoring database..."
    gunzip -c "$backup_file" | PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME"
    
    if [ $? -eq 0 ]; then
        log "Database restored successfully"
    else
        error "Database restore failed"
        exit 1
    fi
}

# Main backup function
perform_backup() {
    log "Starting Mill Management System backup..."
    
    # Create backup
    if create_backup; then
        # Find the latest backup file
        latest_backup=$(ls -t "$BACKUP_DIR"/mill_backup_*.sql.gz 2>/dev/null | head -1)
        
        if [ -n "$latest_backup" ]; then
            # Upload to S3
            upload_to_s3 "$latest_backup"
            
            # Upload metadata
            metadata_file="${latest_backup}.meta"
            if [ -f "$metadata_file" ]; then
                upload_to_s3 "$metadata_file"
            fi
        fi
        
        # Cleanup old backups
        cleanup_old_backups
        
        log "Backup completed successfully"
    else
        error "Backup failed"
        exit 1
    fi
}

# Main script logic
case "${1:-backup}" in
    "backup")
        perform_backup
        ;;
    "restore")
        restore_backup "$2"
        ;;
    "list")
        list_backups
        ;;
    "cleanup")
        cleanup_old_backups
        ;;
    "test")
        log "Testing backup system..."
        perform_backup
        ;;
    *)
        echo "Usage: $0 {backup|restore <file>|list|cleanup|test}"
        echo ""
        echo "Commands:"
        echo "  backup   - Create a new backup (default)"
        echo "  restore  - Restore from backup file"
        echo "  list     - List available backups"
        echo "  cleanup  - Clean up old backups"
        echo "  test     - Test backup system"
        exit 1
        ;;
esac 