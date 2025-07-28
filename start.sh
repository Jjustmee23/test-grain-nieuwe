#!/bin/bash

# Start cron service
service cron start

# Add cron job for power status updates every 5 minutes
echo "*/5 * * * * cd /app && python manage.py auto_update_power_status --create-events >> /var/log/cron.log 2>&1" | crontab -

# Start Django development server
python manage.py runserver 0.0.0.0:8000 