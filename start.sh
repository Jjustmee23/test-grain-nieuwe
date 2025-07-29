#!/bin/bash

# Start cron service
service cron start

# Start Django development server
python manage.py runserver 0.0.0.0:8000 