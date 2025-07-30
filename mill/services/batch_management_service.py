#!/usr/bin/env python3
"""
🏭 UC300 Batch Management Service
Complete batch management voor UC300 devices

Functionaliteit:
- Start nieuwe batches
- Stop actieve batches
- Batch overlap handling (vorige stop automatisch)
- Counter reset per batch
- Batch production tracking
"""

from datetime import datetime
from django.utils import timezone
from django.db import connections, transaction
from mill.models import Device, UC300BatchStatus, CounterResetLog, UC300PilotStatus
import logging

logger = logging.getLogger(__name__)

class BatchManagementService:
    
    def __init__(self):
        self.logger = logger
    
    def log(self, message, level="INFO"):
        """Enhanced logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {'INFO': '📋', 'SUCCESS': '✅', 'WARNING': '⚠️', 'ERROR': '❌'}
        icon = icons.get(level, '📋')
        print(f"[{timestamp}] {icon} {message}")
        
        # Also use Django logger
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)
    
    def get_current_counter_value(self, device_id):
        """Get current counter value from MQTT data"""
        try:
            device = Device.objects.get(id=device_id)
            selected_counter = device.selected_counter
            
            with connections['counter'].cursor() as cursor:
                counter_column = selected_counter  # e.g., 'counter_2'
                query = f"""
                    SELECT {counter_column}, timestamp
                    FROM mqtt_data 
                    WHERE counter_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """
                cursor.execute(query, (device_id,))
                result = cursor.fetchone()
                
                if result:
                    counter_value, timestamp = result
                    value = counter_value if counter_value is not None else 0
                    return value, timestamp
                else:
                    return 0, None
                    
        except Exception as e:
            self.log(f"Error getting counter for {device_id}: {str(e)}", "ERROR")
            return 0, None
    
    def get_active_batch(self, device_id):
        """Get active batch for device"""
        try:
            device = Device.objects.get(id=device_id)
            active_batch = UC300BatchStatus.objects.filter(
                device=device,
                is_active=True
            ).first()
            
            return active_batch
            
        except Exception as e:
            self.log(f"Error getting active batch for {device_id}: {str(e)}", "ERROR")
            return None
    
    def stop_active_batch(self, device_id, reason="new_batch_starting"):
        """Stop any active batch for device"""
        try:
            active_batch = self.get_active_batch(device_id)
            
            if active_batch:
                # Get current counter value
                end_counter, timestamp = self.get_current_counter_value(device_id)
                
                # Update batch
                active_batch.batch_end_time = timezone.now()
                active_batch.end_counter_value = end_counter
                active_batch.is_active = False
                active_batch.notes = f"{active_batch.notes or ''}\nStopped: {reason}"
                active_batch.save()
                
                # Calculate batch production
                if active_batch.start_counter_value is not None:
                    batch_production = max(0, end_counter - active_batch.start_counter_value)
                else:
                    batch_production = end_counter
                
                self.log(f"Stopped batch '{active_batch.batch_name}': Production = {batch_production}")
                self.log(f"Counter: {active_batch.start_counter_value} → {end_counter}")
                
                return active_batch
            else:
                self.log(f"No active batch found for device {device_id}")
                return None
                
        except Exception as e:
            self.log(f"Error stopping active batch: {str(e)}", "ERROR")
            return None
    
    def start_new_batch(self, device_id, batch_name, reset_counter=True):
        """Start new batch for device"""
        try:
            device = Device.objects.get(id=device_id)
            
            self.log(f"🏭 Starting new batch '{batch_name}' for {device.name}")
            
            # Step 1: Stop any active batch
            stopped_batch = self.stop_active_batch(device_id, "new_batch_starting")
            if stopped_batch:
                self.log(f"Stopped previous batch: {stopped_batch.batch_name}")
            
            # Step 2: Get current counter value before reset
            start_counter, timestamp = self.get_current_counter_value(device_id)
            
            # Step 3: Execute counter reset if requested
            reset_log = None
            if reset_counter:
                reset_log = self.execute_counter_reset(device_id, f"batch_start_{batch_name}")
                # After reset, start counter should be 0
                start_counter = 0
            
            # Step 4: Create new batch
            new_batch = UC300BatchStatus.objects.create(
                device=device,
                batch_name=batch_name,
                batch_start_time=timezone.now(),
                is_active=True,
                start_counter_value=start_counter,
                notes=f"Started with counter reset: {reset_counter}"
            )
            
            self.log(f"✅ New batch created: ID {new_batch.id}")
            self.log(f"Start counter: {start_counter}")
            if reset_log:
                self.log(f"Reset log: ID {reset_log.id}")
            
            return new_batch
            
        except Exception as e:
            self.log(f"Error starting new batch: {str(e)}", "ERROR")
            return None
    
    def execute_counter_reset(self, device_id, reason):
        """Execute counter reset using real UC300 MQTT service"""
        try:
            # Import the new UC300 MQTT service
            from mill.services.uc300_mqtt_service import get_uc300_mqtt_service
            
            self.log(f"🔄 Executing UC300 reset with real MQTT commands")
            
            # Use the real UC300 MQTT service
            mqtt_service = get_uc300_mqtt_service()
            reset_log = mqtt_service.send_reset_command(device_id, reason)
            
            if reset_log:
                self.log(f"✅ UC300 reset successful: ID {reset_log.id}")
                self.log(f"📡 Real MQTT command sent with HEX payload")
                return reset_log
            else:
                self.log(f"❌ UC300 reset failed", "ERROR")
                return None
            
        except Exception as e:
            self.log(f"Error executing UC300 reset: {str(e)}", "ERROR")
            return None
    
    def get_batch_status_overview(self, device_id):
        """Get complete batch status for device"""
        try:
            device = Device.objects.get(id=device_id)
            
            # Active batch
            active_batch = self.get_active_batch(device_id)
            
            # Recent batches (last 5)
            recent_batches = UC300BatchStatus.objects.filter(
                device=device
            ).order_by('-batch_start_time')[:5]
            
            # Current counter
            current_counter, timestamp = self.get_current_counter_value(device_id)
            
            status = {
                'device': device,
                'active_batch': active_batch,
                'recent_batches': list(recent_batches),
                'current_counter': current_counter,
                'counter_timestamp': timestamp
            }
            
            return status
            
        except Exception as e:
            self.log(f"Error getting batch status: {str(e)}", "ERROR")
            return None
    
    def calculate_batch_production(self, batch_id):
        """Calculate current production for active batch"""
        try:
            batch = UC300BatchStatus.objects.get(id=batch_id)
            
            if batch.is_active:
                # Get current counter
                current_counter, timestamp = self.get_current_counter_value(batch.device.id)
                
                if batch.start_counter_value is not None:
                    current_production = max(0, current_counter - batch.start_counter_value)
                else:
                    current_production = current_counter
                
                return current_production
            else:
                # Completed batch
                if batch.end_counter_value is not None and batch.start_counter_value is not None:
                    return max(0, batch.end_counter_value - batch.start_counter_value)
                else:
                    return 0
                    
        except Exception as e:
            self.log(f"Error calculating batch production: {str(e)}", "ERROR")
            return 0
    
    def list_available_devices_for_batch(self):
        """List devices that can use batch system"""
        try:
            # Only UC300 pilot devices can use batch system
            pilot_devices = Device.objects.filter(
                pilot_status__is_pilot_enabled=True,
                pilot_status__batch_reset_enabled=True
            ).select_related('pilot_status')
            
            return list(pilot_devices)
            
        except Exception as e:
            self.log(f"Error listing batch devices: {str(e)}", "ERROR")
            return []
    
    def show_batch_dashboard(self, device_id=None):
        """Show complete batch dashboard"""
        self.log("🏭 BATCH MANAGEMENT DASHBOARD")
        print("=" * 60)
        
        if device_id:
            # Show specific device
            status = self.get_batch_status_overview(device_id)
            if status:
                device = status['device']
                active_batch = status['active_batch']
                
                print(f"Device: {device.name} ({device.id})")
                print(f"Current Counter: {status['current_counter']}")
                
                if active_batch:
                    print(f"🟢 ACTIVE BATCH: {active_batch.batch_name}")
                    print(f"   Started: {active_batch.batch_start_time}")
                    print(f"   Start Counter: {active_batch.start_counter_value}")
                    current_prod = self.calculate_batch_production(active_batch.id)
                    print(f"   Current Production: {current_prod}")
                else:
                    print("⚪ No active batch")
                
                print(f"\nRecent Batches:")
                for batch in status['recent_batches'][:3]:
                    status_icon = "🟢" if batch.is_active else "⚪"
                    production = self.calculate_batch_production(batch.id)
                    print(f"   {status_icon} {batch.batch_name}: {production} units")
        else:
            # Show all batch-enabled devices
            devices = self.list_available_devices_for_batch()
            
            print(f"Batch-Enabled Devices: {len(devices)}")
            
            for device in devices:
                active_batch = self.get_active_batch(device.id)
                status_icon = "🟢" if active_batch else "⚪"
                batch_name = active_batch.batch_name if active_batch else "No active batch"
                print(f"   {status_icon} {device.name}: {batch_name}")
        
        print("=" * 60) 