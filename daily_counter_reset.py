#!/usr/bin/env python3
"""
Daily Counter Reset Script - UC300 Devices
Automatically resets UC300 device counters at configured times (e.g., 23:59)
"""

import os
import sys
import django
import logging
from datetime import time, datetime
from django.utils import timezone

# Add the project root to Python path
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Setup Django
django.setup()

from mill.models import UC300PilotStatus, Device
from mill.services.uc300_mqtt_service import get_uc300_mqtt_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/daily_counter_reset.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def should_reset_now(device_reset_time):
    """
    Check if device should be reset now based on configured time
    """
    if not device_reset_time:
        return False
    
    current_time = timezone.now().time()
    
    # Allow 5 minute window around reset time
    reset_hour = device_reset_time.hour
    reset_minute = device_reset_time.minute
    
    current_hour = current_time.hour
    current_minute = current_time.minute
    
    # Check if current time is within 5 minutes of reset time
    if current_hour == reset_hour:
        if abs(current_minute - reset_minute) <= 2:
            return True
    
    return False

def execute_daily_resets():
    """
    Execute daily counter resets for UC300 pilot devices
    """
    logger.info("🕒 STARTING DAILY COUNTER RESET PROCESS")
    logger.info("=" * 60)
    
    # Get all UC300 pilot devices with daily reset enabled
    pilot_devices = UC300PilotStatus.objects.filter(
        is_pilot_enabled=True,
        use_reset_logic=True,
        daily_reset_time__isnull=False
    )
    
    logger.info(f"📊 Found {pilot_devices.count()} UC300 pilot devices with reset time configured")
    
    reset_count = 0
    error_count = 0
    
    # Initialize MQTT service
    try:
        mqtt_service = get_uc300_mqtt_service()
        logger.info("📡 UC300 MQTT service initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize MQTT service: {e}")
        return False
    
    for pilot in pilot_devices:
        device = pilot.device
        device_name = device.name
        device_id = device.name  # Assuming device.name contains the device ID
        reset_time = pilot.daily_reset_time
        
        logger.info(f"\n🎯 Processing device: {device_name}")
        logger.info(f"   Reset time configured: {reset_time}")
        
        # Check if this device should be reset now
        if should_reset_now(reset_time):
            logger.info(f"   ⏰ Reset time reached - executing reset")
            
            try:
                # Execute the reset
                reset_log = mqtt_service.send_reset_command(device_id, "daily_auto")
                
                if reset_log:
                    logger.info(f"   ✅ Reset successful - Log ID: {reset_log.id}")
                    logger.info(f"   📡 MQTT HEX command sent to UC300")
                    reset_count += 1
                else:
                    logger.error(f"   ❌ Reset failed - no reset log created")
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"   ❌ Reset failed with error: {e}")
                error_count += 1
        else:
            current_time = timezone.now().time()
            logger.info(f"   ⏳ Not reset time yet (current: {current_time})")
    
    # Summary
    logger.info(f"\n📊 DAILY RESET SUMMARY:")
    logger.info(f"   ✅ Successful resets: {reset_count}")
    logger.info(f"   ❌ Failed resets: {error_count}")
    logger.info(f"   📱 Total devices processed: {pilot_devices.count()}")
    
    if reset_count > 0:
        logger.info(f"🎉 Daily counter reset process completed successfully!")
    else:
        logger.info(f"⏳ No devices needed reset at this time")
    
    return reset_count > 0

def main():
    """Main execution function"""
    try:
        success = execute_daily_resets()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"💥 Critical error in daily reset process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 