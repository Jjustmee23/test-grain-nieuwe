#!/bin/bash

# Raw Data Sync Management Script
# This script helps manage the raw_data sync daemon

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Function to show usage
show_usage() {
    echo "Raw Data Sync Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     - Start the raw data sync daemon"
    echo "  stop      - Stop the raw data sync daemon"
    echo "  restart   - Restart the raw data sync daemon"
    echo "  status    - Show status of the daemon"
    echo "  logs      - Show daemon logs"
    echo "  sync-now  - Run a manual sync"
    echo "  test      - Test the sync functionality"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs"
    echo "  $0 sync-now"
}

# Function to check if daemon is running
is_daemon_running() {
    docker-compose ps raw-data-sync | grep -q "Up"
}

# Function to start the daemon
start_daemon() {
    print_header "Starting Raw Data Sync Daemon"
    
    if is_daemon_running; then
        print_warning "Daemon is already running"
        return 0
    fi
    
    print_status "Starting daemon with 5-minute sync interval..."
    docker-compose --profile sync up raw-data-sync -d
    
    if is_daemon_running; then
        print_status "Daemon started successfully"
        print_status "Next sync will occur in 5 minutes"
    else
        print_error "Failed to start daemon"
        return 1
    fi
}

# Function to stop the daemon
stop_daemon() {
    print_header "Stopping Raw Data Sync Daemon"
    
    if ! is_daemon_running; then
        print_warning "Daemon is not running"
        return 0
    fi
    
    print_status "Stopping daemon..."
    docker-compose stop raw-data-sync
    
    if ! is_daemon_running; then
        print_status "Daemon stopped successfully"
    else
        print_error "Failed to stop daemon"
        return 1
    fi
}

# Function to restart the daemon
restart_daemon() {
    print_header "Restarting Raw Data Sync Daemon"
    stop_daemon
    sleep 2
    start_daemon
}

# Function to show status
show_status() {
    print_header "Raw Data Sync Daemon Status"
    
    if is_daemon_running; then
        print_status "Daemon is RUNNING"
        echo ""
        print_status "Container details:"
        docker-compose ps raw-data-sync
        echo ""
        print_status "Recent logs:"
        docker-compose logs --tail=10 raw-data-sync
    else
        print_warning "Daemon is NOT RUNNING"
        echo ""
        print_status "Available containers:"
        docker-compose ps
    fi
}

# Function to show logs
show_logs() {
    print_header "Raw Data Sync Daemon Logs"
    
    if is_daemon_running; then
        docker-compose logs -f raw-data-sync
    else
        print_warning "Daemon is not running"
        print_status "Showing last 50 lines of logs:"
        docker-compose logs --tail=50 raw-data-sync
    fi
}

# Function to run manual sync
run_manual_sync() {
    print_header "Running Manual Sync"
    
    print_status "Checking for new data..."
    docker-compose exec web python manage.py sync_raw_data --dry-run
    
    echo ""
    print_status "Running sync..."
    docker-compose exec web python manage.py sync_raw_data
}

# Function to test sync functionality
test_sync() {
    print_header "Testing Sync Functionality"
    
    print_status "Testing dry run..."
    docker-compose exec web python manage.py sync_raw_data --dry-run
    
    echo ""
    print_status "Testing raw data analysis..."
    docker-compose exec web python manage.py analyze_raw_data --show-sample
}

# Main script logic
case "${1:-help}" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        restart_daemon
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    sync-now)
        run_manual_sync
        ;;
    test)
        test_sync
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac 