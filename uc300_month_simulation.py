#!/usr/bin/env python3
"""
UC300 Month Simulation Script
============================
Simulates 1 month of UC300 device operation with realistic production cycles,
including work schedule (no Friday work), random breakdowns, and UC300 resets.

Device: 6445C44843460016
Period: 1 month ago → now
Work Schedule: Monday-Thursday (no Friday)
Breakdowns: Random 1-4 day periods
Reset Logic: Daily 23:59 + breakdown periods
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta, time
from django.utils import timezone
import pytz

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mill.models import Device, RawDataCounter, ProductionData, CounterResetLog, UC300PilotStatus
from django.db import transaction, connections

class UC300MonthSimulation:
    def __init__(self, device_id='6445C44843460016'):
        self.device_id = device_id
        self.device = None
        self.simulation_start = timezone.now() - timedelta(days=30)
        self.simulation_end = timezone.now()
        self.current_counter_value = 0
        self.daily_production_range = (800, 1500)  # Realistic daily production
        self.breakdown_probability = 0.15  # 15% chance per week
        self.breakdown_duration_range = (1, 4)  # 1-4 days
        
        # Work schedule: Monday=0, Friday=4
        self.work_days = [0, 1, 2, 3]  # Mon, Tue, Wed, Thu (no Friday)
        
        print("🏭 UC300 MONTH SIMULATION STARTING")
        print("=" * 50)
        print(f"📱 Device: {device_id}")
        print(f"📅 Period: {self.simulation_start.strftime('%Y-%m-%d')} → {self.simulation_end.strftime('%Y-%m-%d')}")
        print(f"⚙️ Work Days: Monday-Thursday (no Friday)")
        print(f"🔧 Breakdowns: {self.breakdown_probability*100}% chance, {self.breakdown_duration_range[0]}-{self.breakdown_duration_range[1]} days")
        print(f"🔄 Reset Logic: Daily 23:59 + breakdown recovery")

    def setup_device(self):
        """Setup or get the simulation device"""
        try:
            self.device = Device.objects.get(id=self.device_id)
            print(f"✅ Found existing device: {self.device.name}")
        except Device.DoesNotExist:
            print(f"⚠️ Device {self.device_id} not found - creating simulation device")
            # We'll assume device exists or user will create it
            return False
        
        # Setup UC300 pilot status
        pilot_status, created = UC300PilotStatus.objects.get_or_create(
            device=self.device,
            defaults={
                'is_pilot_enabled': True,
                'pilot_start_date': self.simulation_start,
                'use_reset_logic': True,
                'daily_reset_time': time(23, 59),
                'batch_reset_enabled': False
            }
        )
        
        if created:
            print(f"✅ Created UC300 pilot status for device")
        else:
            print(f"✅ Updated UC300 pilot status for device")
            pilot_status.is_pilot_enabled = True
            pilot_status.use_reset_logic = True
            pilot_status.save()
        
        return True

    def generate_breakdown_schedule(self):
        """Generate random breakdown periods over the month"""
        breakdowns = []
        current_date = self.simulation_start.date()
        
        while current_date < self.simulation_end.date():
            # Check for breakdown (weekly probability)
            if random.random() < self.breakdown_probability:
                breakdown_duration = random.randint(*self.breakdown_duration_range)
                breakdown_start = current_date
                breakdown_end = current_date + timedelta(days=breakdown_duration)
                
                breakdowns.append({
                    'start': breakdown_start,
                    'end': breakdown_end,
                    'duration': breakdown_duration,
                    'reason': random.choice([
                        'maintenance', 'equipment_failure', 'power_outage', 
                        'supply_shortage', 'technical_issue'
                    ])
                })
                
                # Skip ahead past breakdown
                current_date = breakdown_end + timedelta(days=1)
            else:
                current_date += timedelta(days=7)  # Check next week
        
        print(f"\n🔧 BREAKDOWN SCHEDULE ({len(breakdowns)} periods):")
        for i, breakdown in enumerate(breakdowns, 1):
            duration = breakdown['duration']
            reason = breakdown['reason']
            start_str = breakdown['start'].strftime('%Y-%m-%d')
            end_str = breakdown['end'].strftime('%Y-%m-%d')
            print(f"   {i}. {start_str} → {end_str} ({duration} days) - {reason}")
        
        return breakdowns

    def is_work_day(self, date, breakdowns):
        """Check if given date is a work day (considering schedule and breakdowns)"""
        # Check if it's a work day (Mon-Thu)
        if date.weekday() not in self.work_days:
            return False, "weekend_schedule"
        
        # Check if it's during a breakdown
        for breakdown in breakdowns:
            if breakdown['start'] <= date <= breakdown['end']:
                return False, f"breakdown_{breakdown['reason']}"
        
        return True, "normal_work"

    def generate_daily_production(self, date, work_status):
        """Generate realistic daily production based on work status"""
        if work_status != "normal_work":
            return 0
        
        # Base production with some daily variation
        base_production = random.randint(*self.daily_production_range)
        
        # Day of week variation (Monday might be slower startup)
        day_multipliers = {
            0: 0.85,  # Monday (slower start)
            1: 1.0,   # Tuesday
            2: 1.1,   # Wednesday (peak)
            3: 0.95   # Thursday
        }
        
        multiplier = day_multipliers.get(date.weekday(), 1.0)
        daily_production = int(base_production * multiplier)
        
        return daily_production

    def create_mqtt_data_points(self, date, daily_production):
        """Create realistic MQTT data points throughout the day"""
        data_points = []
        
        if daily_production == 0:
            # No production day - just maintain current counter
            timestamp = timezone.make_aware(
                datetime.combine(date, time(12, 0)), 
                timezone.get_current_timezone()
            )
            data_points.append({
                'timestamp': timestamp,
                'counter_1': None,
                'counter_2': self.current_counter_value,
                'counter_3': None,
                'counter_4': None
            })
            return data_points
        
        # Production day - simulate 5-minute intervals from 08:00 to 18:00
        start_time = time(8, 0)
        end_time = time(18, 0)
        
        # Calculate production per 5-minute interval
        work_minutes = 10 * 60  # 10 hours * 60 minutes
        intervals_count = work_minutes // 5  # 5-minute intervals
        production_per_interval = daily_production / intervals_count
        
        current_time = start_time
        interval_counter = self.current_counter_value
        
        while current_time <= end_time:
            timestamp = timezone.make_aware(
                datetime.combine(date, current_time),
                timezone.get_current_timezone()
            )
            
            # Add production for this interval
            interval_counter += int(production_per_interval + random.uniform(-0.5, 0.5))
            
            data_points.append({
                'timestamp': timestamp,
                'counter_1': None,
                'counter_2': interval_counter,
                'counter_3': None,
                'counter_4': None
            })
            
            # Next 5-minute interval
            current_datetime = datetime.combine(date, current_time)
            current_datetime += timedelta(minutes=5)
            current_time = current_datetime.time()
        
        # Update current counter for next day
        self.current_counter_value = interval_counter
        
        return data_points

    def create_reset_event(self, date, reason="daily_reset"):
        """Create a UC300 reset event"""
        reset_timestamp = timezone.make_aware(
            datetime.combine(date, time(23, 59)),
            timezone.get_current_timezone()
        )
        
        reset_log = CounterResetLog.objects.create(
            device=self.device,
            reset_timestamp=reset_timestamp,
            counter_1_before=None,
            counter_2_before=self.current_counter_value,
            counter_3_before=None,
            counter_4_before=None,
            reset_reason=reason,
            reset_successful=True,
            notes=f"UC300 Simulation Reset - {reason} at {reset_timestamp}"
        )
        
        # Reset counter to 0
        self.current_counter_value = 0
        
        return reset_log

    def calculate_production_data(self, date, daily_production):
        """Calculate and store production data"""
        # For UC300 devices with reset logic, daily production = current counter value
        from django.utils import timezone
        
        # Set specific time for the production data (end of day)
        production_timestamp = timezone.make_aware(
            datetime.combine(date, time(23, 58)),
            timezone.get_current_timezone()
        )
        
        production_data = {
            'device': self.device,
            'daily_production': daily_production,
            'weekly_production': 0,  # Will be calculated by cumulative logic
            'monthly_production': 0,  # Will be calculated by cumulative logic
            'yearly_production': 0   # Will be calculated by cumulative logic
        }
        
        # Check if entry exists for today (within the same day)
        start_of_day = timezone.make_aware(
            datetime.combine(date, time(0, 0)),
            timezone.get_current_timezone()
        )
        end_of_day = timezone.make_aware(
            datetime.combine(date, time(23, 59, 59)),
            timezone.get_current_timezone()
        )
        
        existing = ProductionData.objects.filter(
            device=self.device,
            created_at__gte=start_of_day,
            created_at__lte=end_of_day
        ).first()
        
        if existing:
            existing.daily_production = daily_production
            existing.save()
            return existing
        else:
            # Create new entry with specific timestamp
            production_entry = ProductionData.objects.create(**production_data)
            # Manually set the created_at to our desired timestamp
            production_entry.created_at = production_timestamp
            production_entry.save()
            return production_entry

    def run_simulation(self):
        """Run the complete month simulation"""
        if not self.setup_device():
            print("❌ Device setup failed")
            return False
        
        # Generate breakdown schedule
        breakdowns = self.generate_breakdown_schedule()
        
        print(f"\n🚀 STARTING SIMULATION")
        print("=" * 30)
        
        current_date = self.simulation_start.date()
        day_count = 0
        work_days = 0
        breakdown_days = 0
        weekend_days = 0
        total_production = 0
        reset_count = 0
        
        with transaction.atomic():
            while current_date < self.simulation_end.date():
                day_count += 1
                
                # Check work status
                is_work, work_status = self.is_work_day(current_date, breakdowns)
                
                # Generate daily production
                daily_production = self.generate_daily_production(current_date, work_status)
                
                # Create MQTT data points
                mqtt_points = self.create_mqtt_data_points(current_date, daily_production)
                
                # Insert MQTT data directly to counter database
                for point in mqtt_points:
                    with connections['counter'].cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO mqtt_data (counter_id, timestamp, counter_1, counter_2, counter_3, counter_4)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            self.device_id,
                            point['timestamp'],
                            point['counter_1'],
                            point['counter_2'],
                            point['counter_3'],
                            point['counter_4']
                        ))
                
                # Calculate production data
                production_entry = self.calculate_production_data(current_date, daily_production)
                
                # Create reset event if work day or breakdown recovery
                if is_work or (work_status.startswith("breakdown") and current_date == current_date):
                    reset_reason = "daily_reset" if is_work else f"breakdown_recovery_{work_status.split('_')[1]}"
                    reset_log = self.create_reset_event(current_date, reset_reason)
                    reset_count += 1
                
                # Update counters
                if is_work:
                    work_days += 1
                    total_production += daily_production
                elif work_status.startswith("breakdown"):
                    breakdown_days += 1
                else:
                    weekend_days += 1
                
                # Progress indication
                if day_count % 5 == 0:
                    print(f"📅 Day {day_count}/30: {current_date} ({work_status}) - Production: {daily_production}")
                
                current_date += timedelta(days=1)
        
        # Final summary
        print(f"\n✅ SIMULATION COMPLETED")
        print("=" * 30)
        print(f"📊 Total Days: {day_count}")
        print(f"⚙️ Work Days: {work_days}")
        print(f"🔧 Breakdown Days: {breakdown_days}")
        print(f"📅 Weekend Days: {weekend_days}")
        print(f"🏭 Total Production: {total_production:,}")
        print(f"📈 Average Daily: {total_production//work_days if work_days > 0 else 0:,}")
        print(f"🔄 Reset Events: {reset_count}")
        print(f"📡 MQTT Points: {day_count * 120} (avg)")  # ~120 points per day
        
        return True

def main():
    """Main simulation function"""
    print("🕰️ UC300 MONTH SIMULATION")
    print("=" * 50)
    
    simulator = UC300MonthSimulation('6445C44843460016')
    success = simulator.run_simulation()
    
    if success:
        print(f"\n🎉 SIMULATION SUCCESS!")
        print(f"Database gevuld met 1 maand realistische UC300 data!")
        print(f"Device 6445C44843460016 heeft nu complete productie historie! 🚀")
    else:
        print(f"\n❌ SIMULATION FAILED!")
    
    return success

if __name__ == "__main__":
    main() 