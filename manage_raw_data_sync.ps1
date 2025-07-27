# Raw Data Sync Management Script for Windows PowerShell
# This script helps manage the raw_data sync daemon

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"
$White = "White"

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

function Write-Header {
    param([string]$Message)
    Write-Host "=== $Message ===" -ForegroundColor $Blue
}

# Function to show usage
function Show-Usage {
    Write-Host "Raw Data Sync Management Script" -ForegroundColor $White
    Write-Host ""
    Write-Host "Usage: .\manage_raw_data_sync.ps1 [COMMAND]" -ForegroundColor $White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor $White
    Write-Host "  start     - Start the raw data sync daemon" -ForegroundColor $White
    Write-Host "  stop      - Stop the raw data sync daemon" -ForegroundColor $White
    Write-Host "  restart   - Restart the raw data sync daemon" -ForegroundColor $White
    Write-Host "  status    - Show status of the daemon" -ForegroundColor $White
    Write-Host "  logs      - Show daemon logs" -ForegroundColor $White
    Write-Host "  sync-now  - Run a manual sync" -ForegroundColor $White
    Write-Host "  test      - Test the sync functionality" -ForegroundColor $White
    Write-Host "  help      - Show this help message" -ForegroundColor $White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor $White
    Write-Host "  .\manage_raw_data_sync.ps1 start" -ForegroundColor $White
    Write-Host "  .\manage_raw_data_sync.ps1 logs" -ForegroundColor $White
    Write-Host "  .\manage_raw_data_sync.ps1 sync-now" -ForegroundColor $White
}

# Function to check if daemon is running
function Test-DaemonRunning {
    $result = docker-compose ps raw-data-sync 2>$null
    return $result -match "Up"
}

# Function to start the daemon
function Start-Daemon {
    Write-Header "Starting Raw Data Sync Daemon"
    
    if (Test-DaemonRunning) {
        Write-Warning "Daemon is already running"
        return
    }
    
    Write-Status "Starting daemon with 5-minute sync interval..."
    docker-compose --profile sync up raw-data-sync -d
    
    if (Test-DaemonRunning) {
        Write-Status "Daemon started successfully"
        Write-Status "Next sync will occur in 5 minutes"
    } else {
        Write-Error "Failed to start daemon"
        exit 1
    }
}

# Function to stop the daemon
function Stop-Daemon {
    Write-Header "Stopping Raw Data Sync Daemon"
    
    if (-not (Test-DaemonRunning)) {
        Write-Warning "Daemon is not running"
        return
    }
    
    Write-Status "Stopping daemon..."
    docker-compose stop raw-data-sync
    
    if (-not (Test-DaemonRunning)) {
        Write-Status "Daemon stopped successfully"
    } else {
        Write-Error "Failed to stop daemon"
        exit 1
    }
}

# Function to restart the daemon
function Restart-Daemon {
    Write-Header "Restarting Raw Data Sync Daemon"
    Stop-Daemon
    Start-Sleep -Seconds 2
    Start-Daemon
}

# Function to show status
function Show-Status {
    Write-Header "Raw Data Sync Daemon Status"
    
    if (Test-DaemonRunning) {
        Write-Status "Daemon is RUNNING"
        Write-Host ""
        Write-Status "Container details:"
        docker-compose ps raw-data-sync
        Write-Host ""
        Write-Status "Recent logs:"
        docker-compose logs --tail=10 raw-data-sync
    } else {
        Write-Warning "Daemon is NOT RUNNING"
        Write-Host ""
        Write-Status "Available containers:"
        docker-compose ps
    }
}

# Function to show logs
function Show-Logs {
    Write-Header "Raw Data Sync Daemon Logs"
    
    if (Test-DaemonRunning) {
        docker-compose logs -f raw-data-sync
    } else {
        Write-Warning "Daemon is not running"
        Write-Status "Showing last 50 lines of logs:"
        docker-compose logs --tail=50 raw-data-sync
    }
}

# Function to run manual sync
function Run-ManualSync {
    Write-Header "Running Manual Sync"
    
    Write-Status "Checking for new data..."
    docker-compose exec web python manage.py sync_raw_data --dry-run
    
    Write-Host ""
    Write-Status "Running sync..."
    docker-compose exec web python manage.py sync_raw_data
}

# Function to test sync functionality
function Test-Sync {
    Write-Header "Testing Sync Functionality"
    
    Write-Status "Testing dry run..."
    docker-compose exec web python manage.py sync_raw_data --dry-run
    
    Write-Host ""
    Write-Status "Testing raw data analysis..."
    docker-compose exec web python manage.py analyze_raw_data --show-sample
}

# Main script logic
switch ($Command.ToLower()) {
    "start" {
        Start-Daemon
    }
    "stop" {
        Stop-Daemon
    }
    "restart" {
        Restart-Daemon
    }
    "status" {
        Show-Status
    }
    "logs" {
        Show-Logs
    }
    "sync-now" {
        Run-ManualSync
    }
    "test" {
        Test-Sync
    }
    "help" {
        Show-Usage
    }
    default {
        Write-Error "Unknown command: $Command"
        Write-Host ""
        Show-Usage
        exit 1
    }
} 