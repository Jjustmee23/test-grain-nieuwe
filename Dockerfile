# Use official Python image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_DISABLE_MIGRATIONS False

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc python3-dev gettext cron dos2unix \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt --timeout=100 --retries=5

# Copy the current directory contents into the container at /app
COPY . /app

# Create staticfiles directory
RUN mkdir -p /app/staticfiles

# Compile translations
RUN python manage.py compilemessages

# Collect static files
RUN python manage.py collectstatic --noinput

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define the command to run on container start
CMD ["sh", "-c", "service cron start && echo '*/5 * * * * cd /app && /usr/local/bin/python manage.py auto_update_power_status --create-events >> /var/log/cron.log 2>&1' | crontab - && python manage.py runserver 0.0.0.0:8000"]
