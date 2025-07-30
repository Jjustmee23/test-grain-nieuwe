#!/usr/bin/env python3
"""
UC300 Live Simulation System
============================
Continues simulation from migrated data, behaving like a real UC300 device.
Runs indefinitely to test UC300 reset logic, production calculation, and MQTT integration.

Device: DUMMY_1753878617
Purpose: Long-term testing of UC300 system before rolling out to real devices
"""

import os
import sys
import django
import random
import time
import threading
from datetime import datetime, timedelta, time as dt_time
from django.utils import timezone

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mill.models import Device, ProductionData, CounterResetLog, UC300PilotStatus
from mill.services.uc300_mqtt_service import get_uc300_mqtt_service
from django.db import transaction, connections

class UC300LiveSimulation:
    def __init__(self, device_id='DUMMY_1753878617'):
        self.device_id = device_id
        self.device = Device.objects.get(id=device_id)
        self.running = False
        self.current_counter = 0
        self.daily_production_target = 0
        self.last_reset_time = None
        self.simulation_speed = 1  # 1 = real time, 60 = 1 hour per minute
        
        # Work schedule: Monday-Thursday
        self.work_days = [0, 1, 2, 3]  # Mon, Tue, Wed, Thu
        self.work_start_time = dt_time(8, 0)
        self.work_end_time = dt_time(18, 0)
        self.reset_time = dt_time(23, 59)
        
        print(f"🤖 UC300 Live Simulation Initialized")
        print(f"📱 Device: {self.device.name} ({device_id})")
        print(f"🏭 Factory: {self.device.factory.name}")
        print(f"🏙️ City: {self.device.factory.city.name}")

    def get_current_counter_from_db(self):
        """Get the latest counter value from MQTT data"""
        try:
            with connections['counter'].cursor() as cursor:
                cursor.execute('''
                    SELECT counter_2 
                    FROM mqtt_data 
                    WHERE counter_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''', (self.device_id,))
                
                result = cursor.fetchone()
                return result[0] if result and result[0] is not None else 0
        except Exception as e:
            print(f"⚠️ Error reading counter: {str(e)}")
            return 0

    def is_work_time(self, current_time=None):
        """Check if current time is within work hours and work days"""
        if current_time is None:
            current_time = timezone.now()
        
        # Check if it's a work day (Monday-Thursday)
        if current_time.weekday() not in self.work_days:
            return False, "weekend"
        
        # Check if it's within work hours
        current_time_only = current_time.time()
        if self.work_start_time <= current_time_only <= self.work_end_time:
            return True, "working"
        elif current_time_only >= self.reset_time:
            return False, "after_hours_reset_time"
        else:
            return False, "after_hours"

    def calculate_production_increment(self):
        """Calculate realistic production increment per interval"""
        # Realistic production: 800-1500 per day over 10 hours (600 minutes)
        # That's roughly 1.3-2.5 units per minute, or 6.5-12.5 per 5-minute interval
        base_increment = random.uniform(6, 12)
        
        # Add some variation based on time of day
        current_hour = timezone.now().hour
        
        # Morning startup (slower)
        if 8 <= current_hour <= 9:
            base_increment *= 0.7
        # Peak hours (faster)
        elif 10 <= current_hour <= 15:
            base_increment *= 1.1
        # Evening wind-down (slower)
        elif 16 <= current_hour <= 18:
            base_increment *= 0.8
        
        return int(base_increment + random.uniform(-2, 2))

    def send_mqtt_data(self, counter_value):
        """Simulate sending MQTT data"""
        try:
            with connections['counter'].cursor() as cursor:
                cursor.execute('''
                    INSERT INTO mqtt_data (counter_id, timestamp, counter_2, mobile_signal, start_flag, type, version, end_flag)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    self.device_id,
                    timezone.now(),
                    counter_value,
                    random.randint(20, 31),  # Mobile signal strength
                    126,  # Start flag
                    5,    # Type
                    11,   # Version  
                    126   # End flag
                ))
                
                return True
        except Exception as e:
            print(f"❌ MQTT Error: {str(e)}")
            return False

    def execute_daily_reset(self, reason="daily_auto_reset"):
        """Execute UC300 daily reset"""
        try:
            # Get current counter value before reset
            counter_before = self.current_counter
            
            # Create reset log
            reset_log = CounterResetLog.objects.create(
                device=self.device,
                reset_timestamp=timezone.now(),
                counter_2_before=counter_before,
                reset_reason=reason,
                reset_successful=True,
                notes=f"Live Simulation Auto Reset - Counter: {counter_before} → 0"
            )
            
            # Calculate daily production
            daily_production = counter_before
            
            # Create/update production data
            today = timezone.now().date()
            production_entry, created = ProductionData.objects.get_or_create(
                device=self.device,
                created_at__date=today,
                defaults={
                    'daily_production': daily_production,
                    'weekly_production': 0,
                    'monthly_production': 0,
                    'yearly_production': 0
                }
            )
            
            if not created:
                production_entry.daily_production = daily_production
                production_entry.save()
            
            # Reset counter to 0
            self.current_counter = 0
            self.send_mqtt_data(0)
            
            print(f"🔄 Daily Reset: {counter_before} → 0 (Production: {daily_production})")
            print(f"📊 Reset Log ID: {reset_log.id}")
            
            return reset_log
            
        except Exception as e:
            print(f"❌ Reset Error: {str(e)}")
            return None

    def should_execute_reset(self):
        """Check if it's time to execute daily reset"""
        current_time = timezone.now()
        
        # Check if it's reset time (23:59)
        if current_time.time() >= self.reset_time:
            # Check if we haven't reset today yet
            today = current_time.date()
            today_resets = CounterResetLog.objects.filter(
                device=self.device,
                reset_timestamp__date=today,
                reset_reason__contains="daily"
            ).exists()
            
            return not today_resets
        
        return False

    def run_simulation_cycle(self):
        """Run one simulation cycle (called every 5 minutes in real-time)"""
        current_time = timezone.now()
        is_working, work_status = self.is_work_time(current_time)
        
        print(f"⏰ {current_time.strftime('%Y-%m-%d %H:%M:%S')} - Status: {work_status}")
        
        # Check for daily reset first
        if self.should_execute_reset():
            self.execute_daily_reset()
            return
        
        # If working hours, increment production
        if is_working:
            increment = self.calculate_production_increment()
            self.current_counter += increment
            
            # Send MQTT data
            success = self.send_mqtt_data(self.current_counter)
            if success:
                print(f"📊 Production: +{increment} → {self.current_counter} total")
            else:
                print(f"⚠️ MQTT transmission failed")
        else:
            # Send maintenance MQTT data (counter stays same)
            self.send_mqtt_data(self.current_counter)
            print(f"🔒 Non-work time, counter maintained: {self.current_counter}")

    def start_simulation(self, duration_hours=None):
        """Start the live simulation"""
        print(f"🚀 Starting UC300 Live Simulation")
        print(f"⏰ Simulation Speed: {self.simulation_speed}x")
        if duration_hours:
            print(f"⏱️ Duration: {duration_hours} hours")
        else:
            print(f"⏱️ Duration: Indefinite (until stopped)")
        
        # Initialize current counter from database
        self.current_counter = self.get_current_counter_from_db()
        print(f"📊 Starting Counter Value: {self.current_counter}")
        
        self.running = True
        start_time = timezone.now()
        cycle_count = 0
        
        try:
            while self.running:
                cycle_count += 1
                
                # Run simulation cycle
                self.run_simulation_cycle()
                
                # Check duration limit
                if duration_hours:
                    elapsed = (timezone.now() - start_time).total_seconds() / 3600
                    if elapsed >= duration_hours:
                        print(f"⏱️ Duration limit reached ({duration_hours} hours)")
                        break
                
                # Progress indicator
                if cycle_count % 12 == 0:  # Every hour (12 * 5 minutes)
                    elapsed_minutes = cycle_count * 5
                    print(f"📊 Simulation running for {elapsed_minutes} minutes ({cycle_count} cycles)")
                
                # Wait for next cycle (5 minutes in real-time, adjusted by simulation speed)
                sleep_time = (5 * 60) / self.simulation_speed
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print(f"\n⏹️ Simulation stopped by user")
        except Exception as e:
            print(f"\n❌ Simulation error: {str(e)}")
        finally:
            self.running = False
            print(f"🏁 Simulation completed after {cycle_count} cycles")

    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False
        print(f"⏹️ Stopping UC300 Live Simulation")

def main():
    """Main function to run the simulation"""
    print("🤖 UC300 LIVE SIMULATION SYSTEM")
    print("=" * 50)
    
    simulator = UC300LiveSimulation('DUMMY_1753878617')
    
    # Run simulation for 24 hours (for testing)
    # Change to None for indefinite simulation
    simulator.start_simulation(duration_hours=24)
    
    print(f"\n🎉 UC300 Live Simulation Completed!")
    print(f"Device DUMMY_1753878617 has been simulated successfully!")

if __name__ == "__main__":
    main() 