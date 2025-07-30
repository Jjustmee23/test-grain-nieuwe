#!/usr/bin/env python3
"""
🔄 UC300 Device Manager - Device 6445F17627320016
Complete management system voor jouw specifieke device

Functionaliteit:
- Daily reset om 23:59
- Batch management (counter loopt tot batch stop)
- Super admin reset (wis ProductionData)
- Alleen voor device 6445F17627320016
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project-mill-application.settings')
django.setup()

from datetime import datetime, time
from django.utils import timezone
from django.db import connections
from mill.models import Device, CounterResetLog, UC300PilotStatus, ProductionData

class UC300DeviceManager:
    
    def __init__(self):
        self.device_id = "6445F17627320016"
        self.device = None
        
    def log(self, message, level="INFO"):
        """Logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {'INFO': '📋', 'SUCCESS': '✅', 'WARNING': '⚠️', 'ERROR': '❌'}
        icon = icons.get(level, '📋')
        print(f"[{timestamp}] {icon} {message}")
    
    def initialize_device(self):
        """Initialize device and verify setup"""
        try:
            self.device = Device.objects.get(id=self.device_id)
            self.log(f"Device loaded: {self.device.name}")
            return True
        except Device.DoesNotExist:
            self.log(f"Device {self.device_id} not found!", "ERROR")
            return False
    
    def get_current_counter_value(self):
        """Get current counter value from MQTT data"""
        try:
            with connections['counter'].cursor() as cursor:
                query = """
                    SELECT counter_2, timestamp
                    FROM mqtt_data 
                    WHERE counter_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """
                cursor.execute(query, (self.device_id,))
                result = cursor.fetchone()
                
                if result:
                    counter_value, timestamp = result
                    value = counter_value if counter_value is not None else 0
                    self.log(f"Current counter: {value} (at {timestamp})")
                    return value
                else:
                    self.log("No MQTT data found", "WARNING")
                    return 0
                    
        except Exception as e:
            self.log(f"Error getting counter: {str(e)}", "ERROR")
            return 0
    
    def check_batch_status(self):
        """Check if device has active batch"""
        # Voor nu simuleren we dit - later kun je UC300BatchStatus model gebruiken
        self.log("Checking batch status...")
        # Hier zou je checken of er een actieve batch is
        # Voor nu return False (geen actieve batch)
        return False
    
    def daily_reset_check(self):
        """Check if daily reset should happen (23:59)"""
        now = timezone.now()
        current_time = now.time()
        
        # Check if it's 23:59
        reset_time = time(23, 59)
        
        # Voor demo purposes, laten we zeggen dat het reset tijd is als het na 23:50 is
        demo_reset_time = time(23, 50)
        
        if current_time >= demo_reset_time or current_time <= time(0, 10):
            self.log("Daily reset time reached (23:59)", "INFO")
            return True
        else:
            self.log(f"Not reset time yet (current: {current_time}, reset: {reset_time})")
            return False
    
    def execute_reset(self, reason="daily"):
        """Execute counter reset using real UC300 MQTT service"""
        try:
            # Import the new UC300 MQTT service
            from mill.services.uc300_mqtt_service import get_uc300_mqtt_service
            
            self.log(f"🔄 Executing {reason} reset with REAL MQTT commands...")
            
            # Use the real UC300 MQTT service
            mqtt_service = get_uc300_mqtt_service()
            reset_log = mqtt_service.send_reset_command(self.device_id, reason)
            
            if reset_log:
                self.log(f"✅ UC300 reset successful: ID {reset_log.id}", "SUCCESS")
                self.log(f"📡 Real MQTT HEX command sent to UC300", "SUCCESS")
                return reset_log
            else:
                self.log(f"❌ UC300 reset failed", "ERROR")
                return None
            
        except Exception as e:
            self.log(f"Reset failed: {str(e)}", "ERROR")
            return None
    
    def super_admin_reset(self):
        """Super admin function: Clear ALL ProductionData for device"""
        try:
            self.log("🚨 SUPER ADMIN RESET - CLEARING ALL PRODUCTION DATA")
            
            # Count current entries
            current_count = ProductionData.objects.filter(device=self.device).count()
            self.log(f"Found {current_count} ProductionData entries")
            
            if current_count > 0:
                # Delete all production data for this device
                deleted_count, _ = ProductionData.objects.filter(device=self.device).delete()
                self.log(f"Deleted {deleted_count} ProductionData entries", "SUCCESS")
                
                # Also execute counter reset
                reset_log = self.execute_reset("super_admin")
                
                self.log("🎯 SUPER ADMIN RESET COMPLETED", "SUCCESS")
                self.log("Device reset to clean state - ready for fresh start")
                
                return True
            else:
                self.log("No ProductionData to delete")
                return True
                
        except Exception as e:
            self.log(f"Super admin reset failed: {str(e)}", "ERROR")
            return False
    
    def calculate_daily_production_with_increments(self, current_counter):
        """
        Calculate daily production for incremental data (200, 300, 500, etc.)
        
        Logic volgens jouw specs:
        - Als device vandaag gestart op 0, en nu 500 heeft → daily = 500
        - Data komt elke 5 min: 200 → 300 → 500 (normaal oplopend)
        - Als er reset was vandaag → daily = huidige counter waarde
        """
        try:
            # Check for reset today
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start.replace(hour=23, minute=59, second=59)
            
            reset_today = CounterResetLog.objects.filter(
                device=self.device,
                reset_timestamp__range=[today_start, today_end],
                reset_successful=True
            ).first()
            
            if reset_today:
                # Er was reset vandaag - daily = current counter
                daily_production = current_counter
                self.log(f"Reset today → Daily = {daily_production} (direct counter)")
                return daily_production, "RESET_LOGIC"
            else:
                # Geen reset vandaag - check wat de startwaarde was
                # Voor nu, als geen reset = gebruik counter waarde als daily
                daily_production = current_counter
                self.log(f"No reset today → Daily = {daily_production} (accumulated)")
                return daily_production, "ACCUMULATION_LOGIC"
                
        except Exception as e:
            self.log(f"Error calculating production: {str(e)}", "ERROR")
            return 0, "ERROR"
    
    def update_production_data(self):
        """Update ProductionData with correct logic"""
        try:
            current_counter = self.get_current_counter_value()
            daily_production, method = self.calculate_daily_production_with_increments(current_counter)
            
            # Creëer of update ProductionData entry voor vandaag
            today = timezone.now().date()
            
            production_entry, created = ProductionData.objects.get_or_create(
                device=self.device,
                created_at__date=today,
                defaults={
                    'daily_production': daily_production,
                    'weekly_production': daily_production,  # Simplified
                    'monthly_production': daily_production,
                    'yearly_production': daily_production
                }
            )
            
            if not created:
                # Update existing entry
                production_entry.daily_production = daily_production
                production_entry.save()
            
            action = "Created" if created else "Updated"
            self.log(f"{action} ProductionData: Daily = {daily_production}")
            self.log(f"Method: {method}")
            
            return production_entry
            
        except Exception as e:
            self.log(f"Error updating production: {str(e)}", "ERROR")
            return None
    
    def show_device_status(self):
        """Show complete device status"""
        self.log("📊 DEVICE STATUS OVERVIEW")
        print("-" * 50)
        
        # Current counter
        current_counter = self.get_current_counter_value()
        
        # Batch status
        batch_active = self.check_batch_status()
        
        # Recent resets
        recent_resets = CounterResetLog.objects.filter(device=self.device).count()
        
        # Production entries
        production_entries = ProductionData.objects.filter(device=self.device).count()
        
        print(f"Device: {self.device.name}")
        print(f"Current Counter: {current_counter}")
        print(f"Batch Active: {'Yes' if batch_active else 'No'}")
        print(f"Total Resets: {recent_resets}")
        print(f"Production Entries: {production_entries}")
        
        # Pilot status
        pilot_status = getattr(self.device, 'pilot_status', None)
        if pilot_status:
            print(f"Pilot Status: {'ACTIVE' if pilot_status.is_pilot_enabled else 'INACTIVE'}")
            print(f"Daily Reset Time: {pilot_status.daily_reset_time}")
            print(f"Batch Reset Enabled: {pilot_status.batch_reset_enabled}")
        
        print("-" * 50)
    
    def run_device_cycle(self):
        """Run complete device management cycle"""
        self.log("🔄 UC300 DEVICE MANAGEMENT CYCLE")
        print("=" * 60)
        
        if not self.initialize_device():
            return False
        
        # Show current status
        self.show_device_status()
        
        # Check if batch is active
        batch_active = self.check_batch_status()
        
        if batch_active:
            self.log("Batch is active - counter keeps running")
        else:
            # Check if daily reset is needed
            if self.daily_reset_check():
                self.log("Executing daily reset (23:59)")
                self.execute_reset("daily")
            else:
                self.log("No reset needed - normal operation")
        
        # Update production data
        self.update_production_data()
        
        self.log("🎯 DEVICE CYCLE COMPLETED", "SUCCESS")
        return True

def main():
    """Main interface"""
    manager = UC300DeviceManager()
    
    print("🎯 UC300 DEVICE MANAGER")
    print(f"Device: {manager.device_id}")
    print()
    print("Options:")
    print("1. Show device status")
    print("2. Execute manual reset")
    print("3. Super admin reset (CLEAR ALL DATA)")
    print("4. Run device cycle")
    print("5. Update production data")
    print()
    
    try:
        choice = input("Select option (1-5): ").strip()
        
        if not manager.initialize_device():
            return
        
        if choice == "1":
            manager.show_device_status()
            
        elif choice == "2":
            reason = input("Reset reason (manual/daily/batch) [manual]: ").strip() or "manual"
            manager.execute_reset(reason)
            
        elif choice == "3":
            confirm = input("⚠️ This will DELETE ALL ProductionData! Type 'DELETE' to confirm: ")
            if confirm == "DELETE":
                manager.super_admin_reset()
            else:
                print("Super admin reset cancelled")
                
        elif choice == "4":
            manager.run_device_cycle()
            
        elif choice == "5":
            manager.update_production_data()
            
        else:
            print("Invalid option")
            
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 