#!/bin/bash

# Script to update mill_productiondata from raw_data
# This should be run periodically (e.g., every 15 minutes)

cd /home/administrator/project-mill-application

# Update production data
docker exec project-mill-application_web_1 python manage.py populate_production_data

# Log the update
echo "$(date): Production data updated" >> /var/log/mill_production_update.log 