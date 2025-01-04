# simulate_counter_updates.py

import os
import django
import requests
import random
import time
import schedule
from datetime import datetime
import logging

# Configure Logging
logging.basicConfig(
    filename='counter_update.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Django Setup ---
# If you need to access Django models directly, uncomment the following lines.
# However, for this script, we'll use HTTP requests to interact with the API.

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
# django.setup()

# --- Configuration ---
API_BASE_URL = 'http://localhost:8000/api/counter-data/'  # Replace with your actual API base URL
UPDATE_ENDPOINT = API_BASE_URL  # We'll append device_id to this
HIGH_FREQUENCY_PERCENTAGE = 20  # 20% of devices
HIGH_FREQUENCY_INTERVAL_MINUTES = 0.015  # High frequency interval
REGULAR_INTERVAL_MINUTES = 0.030  # Regular frequency interval

# Authentication (if your API requires it)
# For example, if using token authentication:
# API_TOKEN = 'your_api_token_here'
# HEADERS = {
#     'Authorization': f'Token {API_TOKEN}',
#     'Content-Type': 'application/json'
# }

HEADERS = {
    'Content-Type': 'application/json'
}

# --- Helper Functions ---

def get_all_device_ids():
    """
    Fetch all device IDs from the database.
    This function assumes you have an API endpoint that returns all devices.
    If not, you can implement one or fetch device IDs directly from the database.
    """
    devices_api_url = 'http://localhost:8000/api/devices/'  # Replace with your actual devices API endpoint
    try:
        response = requests.get(devices_api_url, headers=HEADERS)
        response.raise_for_status()
        devices = response.json()['devices']  # Assuming the API returns JSON data
        print(devices)
        device_ids = [device['id'] for device in devices]
        logging.info(f'Fetched {len(device_ids)} devices.')
        return device_ids
    except requests.exceptions.RequestException as e:
        logging.error(f'Error fetching devices: {e}')
        return []

def select_high_frequency_devices(device_ids, percentage=20):
    """
    Randomly select a percentage of devices for high-frequency updates.
    """
    high_freq_count = max(1, int(len(device_ids) * percentage / 100))
    high_freq_devices = random.sample(device_ids, high_freq_count)
    logging.info(f'Selected {len(high_freq_devices)} high-frequency devices.')
    return high_freq_devices

def update_counter(device_id):
    """
    Make an API request to update the counter for a specific device.
    """
    url = f'{UPDATE_ENDPOINT}{device_id}/'
    try:
        response = requests.post(url, headers=HEADERS)  # Assuming POST request triggers the update
        response.raise_for_status()
        logging.info(f'Successfully updated counter for Device ID: {device_id}')
    except requests.exceptions.RequestException as e:
        logging.error(f'Error updating counter for Device ID {device_id}: {e}')

def update_regular_devices(device_ids):
    """
    Update counters for regular frequency devices.
    """
    logging.info('Updating regular frequency devices...')
    for device_id in device_ids:
        update_counter(device_id)

def update_high_frequency_devices(high_freq_ids):
    """
    Update counters for high-frequency devices.
    """
    logging.info('Updating high-frequency devices...')
    for device_id in high_freq_ids:
        update_counter(device_id)

# --- Main Simulation Logic ---

def run_simulation():
    # Fetch all device IDs
    device_ids = get_all_device_ids()
    if not device_ids:
        logging.error('No devices found. Exiting simulation.')
        return

    # Select high-frequency devices
    high_freq_devices = select_high_frequency_devices(device_ids, HIGH_FREQUENCY_PERCENTAGE)

    # Determine regular devices
    regular_devices = list(set(device_ids) - set(high_freq_devices))

    # Schedule regular device updates
    schedule.every(REGULAR_INTERVAL_MINUTES).seconds.do(update_regular_devices, device_ids=regular_devices)

    # Schedule high-frequency device updates
    schedule.every(HIGH_FREQUENCY_INTERVAL_MINUTES).seconds.do(update_high_frequency_devices, high_freq_ids=high_freq_devices)

    logging.info('Started simulation scheduler.')

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    logging.info('Starting counter update simulation.')
    run_simulation()
