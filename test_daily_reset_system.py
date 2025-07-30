#!/usr/bin/env python3
"""
Test Daily Reset System Configuration
Verifies that the automatic counter reset system is properly set up
"""

import os
import sys
import django
import subprocess
from datetime import time, datetime

# Add the project root to Python path
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Setup Django
django.setup()

from mill.models import UC300PilotStatus
from django.utils import timezone

def test_cron_configuration():
    """Test if cron job is properly configured"""
    print("🤖 TESTING CRON CONFIGURATION:")
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            cron_lines = result.stdout.strip().split('\n')
            reset_jobs = [line for line in cron_lines if 'daily_counter_reset' in line and '23' in line]
            
            if reset_jobs:
                print(f"   ✅ Cron job found: {reset_jobs[0]}")
                return True
            else:
                print(f"   ❌ No daily reset cron job found")
                return False
        else:
            print(f"   ❌ Could not read crontab")
            return False
    except Exception as e:
        print(f"   ❌ Error checking cron: {e}")
        return False

def test_pilot_devices():
    """Test UC300 pilot devices configuration"""
    print("\n📊 TESTING UC300 PILOT DEVICES:")
    
    pilot_devices = UC300PilotStatus.objects.filter(is_pilot_enabled=True)
    print(f"   Total pilot devices: {pilot_devices.count()}")
    
    reset_devices = pilot_devices.filter(daily_reset_time__isnull=False)
    print(f"   Devices with reset time: {reset_devices.count()}")
    
    reset_23_59 = reset_devices.filter(daily_reset_time__hour=23, daily_reset_time__minute=59)
    print(f"   Devices with 23:59 reset: {reset_23_59.count()}")
    
    if reset_23_59.count() > 0:
        print(f"   ✅ 23:59 reset devices:")
        for device in reset_23_59:
            print(f"      📍 {device.device.name}")
        return True
    else:
        print(f"   ⚠️ No devices configured for 23:59 reset")
        return False

def test_script_execution():
    """Test if the daily reset script exists and is executable"""
    print("\n🔧 TESTING SCRIPT EXECUTION:")
    
    script_path = '/app/daily_counter_reset.py'
    if os.path.exists(script_path):
        print(f"   ✅ Script exists: {script_path}")
        
        if os.access(script_path, os.X_OK):
            print(f"   ✅ Script is executable")
            return True
        else:
            print(f"   ⚠️ Script exists but not executable")
            return False
    else:
        print(f"   ❌ Script not found: {script_path}")
        return False

def simulate_reset_time_check():
    """Simulate what happens at reset time"""
    print("\n⏰ SIMULATING RESET TIME CHECK:")
    
    # Get devices with 23:59 reset
    reset_devices = UC300PilotStatus.objects.filter(
        is_pilot_enabled=True,
        daily_reset_time__hour=23,
        daily_reset_time__minute=59
    )
    
    print(f"   Found {reset_devices.count()} devices that would reset at 23:59")
    
    current_time = timezone.now().time()
    print(f"   Current time: {current_time}")
    
    # Check if any device would reset now (if it were 23:59)
    reset_time = time(23, 59)
    print(f"   Reset time: {reset_time}")
    
    if reset_devices.count() > 0:
        print(f"   ✅ At 23:59, these devices would be reset:")
        for device in reset_devices:
            print(f"      🔄 {device.device.name} (Reset logic: {device.use_reset_logic})")
        return True
    else:
        print(f"   ❌ No devices would be reset at 23:59")
        return False

def main():
    """Main test function"""
    print("🕒 DAILY COUNTER RESET SYSTEM - CONFIGURATION TEST")
    print("=" * 70)
    
    # Run all tests
    tests = [
        ("Cron Configuration", test_cron_configuration),
        ("Pilot Devices", test_pilot_devices), 
        ("Script Execution", test_script_execution),
        ("Reset Time Simulation", simulate_reset_time_check)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ Test failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📋 TEST SUMMARY:")
    print("-" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 DAILY RESET SYSTEM IS FULLY CONFIGURED!")
        print("   ✅ Automatic counter resets will happen at 23:59")
        print("   📡 MQTT commands will be sent to UC300 devices")
        print("   📊 Reset logs will be created in database")
    else:
        print("⚠️ SYSTEM NEEDS ATTENTION:")
        failed_tests = [name for name, result in results if not result]
        for test in failed_tests:
            print(f"   🔧 Fix: {test}")
    
    print(f"\n🔍 NEXT MANUAL TEST:")
    print(f"   docker exec project-mill-application_web_1 python /app/daily_counter_reset.py")
    print(f"   tail -f /var/log/cron_daily_reset.log")

if __name__ == "__main__":
    main() 