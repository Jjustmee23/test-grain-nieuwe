# Raw Data Sync System

## Overview

This system automatically synchronizes data from the `mqtt_data` table in the counter database to the `raw_data` table in the testdb database every 5 minutes. This ensures that the `raw_data` table always contains the latest production data from all devices.

## Components

### 1. Database Tables

- **`mqtt_data`**: Source table in counter database containing real-time MQTT data from devices
- **`raw_data`**: Target table in testdb database (exact copy of `mqtt_data`) used by the application

### 2. Django Models

- **`RawDataCounter`**: Django model for the `raw_data` table in `mill/models.py` (uses default database)

### 3. Management Commands

- **`copy_mqtt_to_raw_data`**: Initial copy of all data from `mqtt_data` to `raw_data`
- **`sync_raw_data`**: Sync new records from `mqtt_data` to `raw_data`
- **`raw_data_sync_daemon`**: Daemon that runs continuous sync every 5 minutes
- **`analyze_raw_data`**: Analyze and display statistics from the `raw_data` table

### 4. Docker Services

- **`raw-data-sync`**: Docker service running the sync daemon
- **`web`**: Main Django application
- **`postgres`**: PostgreSQL databaseqsdqsdqsdqsd

## Quick Start

### 1. Initial Setup

```bash
# Copy all existing data from mqtt_data to raw_data
docker-compose exec web python manage.py copy_mqtt_to_raw_data --drop-existing
```

### 2. Start the Sync Daemon

```bash
# Start the daemon (runs every 5 minutes)
docker-compose --profile sync up raw-data-sync -d
```

### 3. Check Status

```bash
# Check if daemon is running
.\manage_raw_data_sync.ps1 status

# View logs
.\manage_raw_data_sync.ps1 logs
```

## Management Script

Use the PowerShell script `manage_raw_data_sync.ps1` to manage the sync daemon:

```powershell
# Show help
.\manage_raw_data_sync.ps1 help

# Start daemon
.\manage_raw_data_sync.ps1 start

# Stop daemon
.\manage_raw_data_sync.ps1 stop

# Restart daemon
.\manage_raw_data_sync.ps1 restart

# Check status
.\manage_raw_data_sync.ps1 status

# View logs
.\manage_raw_data_sync.ps1 logs

# Run manual sync
.\manage_raw_data_sync.ps1 sync-now

# Test functionality
.\manage_raw_data_sync.ps1 test
```

## Manual Commands

### Sync Commands

```bash
# Dry run (see what would be synced)
docker-compose exec web python manage.py sync_raw_data --dry-run

# Sync new data
docker-compose exec web python manage.py sync_raw_data

# Force sync all data
docker-compose exec web python manage.py sync_raw_data --force-sync-all
```

### Analysis Commands

```bash
# Analyze raw_data table
docker-compose exec web python manage.py analyze_raw_data

# Analyze specific device
docker-compose exec web python manage.py analyze_raw_data --device-id 6445E27562470013

# Show sample data
docker-compose exec web python manage.py analyze_raw_data --show-sample
```

## How It Works

### 1. Initial Copy
- Creates `raw_data` table with exact structure of `mqtt_data`
- Copies all existing records
- Creates indexes and constraints

### 2. Continuous Sync
- Daemon runs every 5 minutes
- Checks for new records in `mqtt_data` (where ID > max ID in `raw_data`)
- Inserts only new records to avoid duplicates
- Logs sync statistics

### 3. Data Structure
The `raw_data` table contains:
- **26 columns** including device ID, timestamp, counter values
- **Counter fields**: counter_1, counter_2, counter_3, counter_4
- **Device identification**: counter_id field
- **Timestamps**: When data was received

## Monitoring

### Check Daemon Status
```bash
docker-compose ps raw-data-sync
```

### View Logs
```bash
# Follow logs in real-time
docker-compose logs -f raw-data-sync

# View last 50 lines
docker-compose logs --tail=50 raw-data-sync
```

### Database Statistics
```bash
# Check record counts
docker-compose exec web python manage.py analyze_raw_data

# Check specific device
docker-compose exec web python manage.py analyze_raw_data --device-id DEVICE_ID
```

## Troubleshooting

### Daemon Not Starting
```bash
# Check if profile is enabled
docker-compose --profile sync ps

# Start manually
docker-compose --profile sync up raw-data-sync -d
```

### Sync Errors
```bash
# Check database connection
docker-compose exec web python manage.py sync_raw_data --dry-run

# Force full sync
docker-compose exec web python manage.py sync_raw_data --force-sync-all
```

### Data Issues
```bash
# Analyze table structure
docker-compose exec web python manage.py analyze_raw_data --show-sample

# Check for specific device data
docker-compose exec web python manage.py analyze_raw_data --device-id DEVICE_ID
```

## Configuration

### Sync Interval
Change the sync interval in `docker-compose.yml`:
```yaml
command: python manage.py raw_data_sync_daemon --interval 300 --log-level INFO
```

### Log Level
Available levels: DEBUG, INFO, WARNING, ERROR
```yaml
command: python manage.py raw_data_sync_daemon --interval 300 --log-level DEBUG
```

## Integration with Application

The `RawDataCounter` model can be used in your Django views:

```python
from mill.models import RawDataCounter

# Get latest data for a device
latest = RawDataCounter.objects.using('default').filter(
    counter_id='6445E27562470013'
).order_by('-timestamp').first()

# Get data by date range
data = RawDataCounter.objects.using('default').filter(
    counter_id='6445E27562470013',
    timestamp__range=[start_date, end_date]
)

# Get counter values
counter_data = RawDataCounter.objects.using('default').filter(
    counter_id='6445E27562470013'
).values('timestamp', 'counter_2').order_by('timestamp')
```

## Performance

- **Sync time**: Typically 1-5 seconds depending on new data volume
- **Memory usage**: Minimal (only processes new records)
- **Database impact**: Low (only INSERT operations)
- **Network**: Uses local Docker network

## Security

- Runs in isolated Docker container
- Uses same database credentials as main application
- No external network access required
- Logs contain no sensitive information

## Maintenance

### Regular Tasks
- Monitor logs for errors
- Check sync statistics weekly
- Verify data integrity monthly

### Backup
The `raw_data` table is automatically backed up with the main database.

### Updates
To update the sync system:
1. Stop the daemon: `.\manage_raw_data_sync.ps1 stop`
2. Update code
3. Restart the daemon: `.\manage_raw_data_sync.ps1 start` 