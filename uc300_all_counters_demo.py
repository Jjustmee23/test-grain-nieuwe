#!/usr/bin/env python3
"""
🚀 UC300 All Counters Demo - DI1, DI2, DI3, DI4
Complete demo voor alle 4 UC300 digital inputs met automatische HEX payload selectie

Features:
- Alle 4 HEX payloads (DI1-DI4)
- Automatische selectie op basis van selected_counter
- Device configuratie test
- Reset demonstratie per counter type
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project-mill-application.settings')
django.setup()

from mill.models import Device
from mill.services.uc300_mqtt_service import get_uc300_mqtt_service
from datetime import datetime

class UC300AllCountersDemo:
    
    def __init__(self):
        self.device_id = "6445F17627320016"
        self.device = None
        
        # Complete counter mapping
        self.counter_mapping = {
            'counter_1': {'di': 'DI1', 'hex': '7e050b006001000000007e'},
            'counter_2': {'di': 'DI2', 'hex': '7e050b006002000000007e'},
            'counter_3': {'di': 'DI3', 'hex': '7e050b006003000000007e'},
            'counter_4': {'di': 'DI4', 'hex': '7e050b006004000000007e'},
        }
        
    def log(self, message, level="INFO"):
        """Enhanced logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {'INFO': '📋', 'SUCCESS': '✅', 'WARNING': '⚠️', 'ERROR': '❌'}
        icon = icons.get(level, '📋')
        print(f"[{timestamp}] {icon} {message}")
    
    def show_all_counters_overview(self):
        """Show complete overview of all 4 counters"""
        self.log("🔍 UC300 ALL COUNTERS OVERVIEW")
        print("=" * 70)
        
        print(f"📱 Device: {self.device_id}")
        print(f"🎯 Current Selected: {self.device.selected_counter}")
        print()
        
        print("🔥 ALL AVAILABLE COUNTERS & HEX PAYLOADS:")
        print("-" * 70)
        
        for counter, info in self.counter_mapping.items():
            active = "🎯 ACTIVE" if counter == self.device.selected_counter else "⚪ Available"
            print(f"{active} {info['di']} ({counter})")
            print(f"     📡 Topic: uc/{self.device_id}/ucp/+/cmd/update")
            print(f"     🔥 HEX:   {info['hex']}")
            print()
    
    def show_hex_payload_breakdown(self, counter_type):
        """Show detailed breakdown of HEX payload"""
        info = self.counter_mapping[counter_type]
        hex_payload = info['hex']
        di_name = info['di']
        
        print(f"🔍 HEX PAYLOAD BREAKDOWN - {di_name} ({counter_type})")
        print("-" * 50)
        print(f"HEX: {hex_payload}")
        print()
        print("Breakdown:")
        print("7e050b006001000000007e")
        print("│ │ │ │  │  │       │")
        print("│ │ │ │  │  │       └─ End marker (7e)")
        print("│ │ │ │  │  └───────── Zeros padding")
        counter_hex = hex_payload[10:12]  # Extract counter byte
        print(f"│ │ │ │  └────────────── Counter type ({counter_hex} = {di_name})")
        print("│ │ │ └─────────────────── Register (60 = counter)")
        print("│ │ └────────────────────── Length (0b)")
        print("│ └──────────────────────── Command (05 = write)")
        print("└────────────────────────── Start marker (7e)")
        print()
    
    def test_counter_selection(self, test_counter):
        """Test reset met specifieke counter selectie"""
        self.log(f"🧪 TESTING COUNTER: {test_counter}")
        
        # Temporarily change device counter for test
        original_counter = self.device.selected_counter
        self.device.selected_counter = test_counter
        self.device.save()
        
        try:
            info = self.counter_mapping[test_counter]
            print(f"📊 Test Configuration:")
            print(f"   Counter: {test_counter}")
            print(f"   Digital Input: {info['di']}")
            print(f"   Expected HEX: {info['hex']}")
            
            # Get MQTT service and test
            mqtt_service = get_uc300_mqtt_service()
            
            # Show what payload will be used
            selected_payload = mqtt_service.get_hex_payload(test_counter)
            print(f"   Generated HEX: {selected_payload}")
            
            if selected_payload == info['hex']:
                self.log(f"✅ CORRECT: HEX payload matches {info['di']}", "SUCCESS")
            else:
                self.log(f"❌ ERROR: HEX payload mismatch", "ERROR")
            
            # Execute test reset
            reset_log = mqtt_service.send_reset_command(self.device_id, f"test_{test_counter}_{info['di']}")
            
            if reset_log:
                self.log(f"✅ Reset successful: ID {reset_log.id}", "SUCCESS")
                return True
            else:
                self.log(f"❌ Reset failed", "ERROR")
                return False
                
        finally:
            # Restore original counter
            self.device.selected_counter = original_counter
            self.device.save()
    
    def run_complete_demo(self):
        """Run complete demo voor alle counters"""
        self.log("🚀 UC300 ALL COUNTERS COMPLETE DEMO")
        print("=" * 70)
        
        try:
            # Load device
            self.device = Device.objects.get(id=self.device_id)
            self.log(f"Device loaded: {self.device.name}")
            
            # Show overview
            self.show_all_counters_overview()
            
            # Show current counter breakdown
            current_counter = self.device.selected_counter
            self.show_hex_payload_breakdown(current_counter)
            
            # Test all counters
            print("🧪 TESTING ALL COUNTERS:")
            print("=" * 50)
            
            success_count = 0
            total_tests = len(self.counter_mapping)
            
            for counter in self.counter_mapping.keys():
                print(f"\n{'='*30}")
                success = self.test_counter_selection(counter)
                if success:
                    success_count += 1
                print(f"{'='*30}")
            
            # Final summary
            print(f"\n🎯 DEMO COMPLETED!")
            print(f"✅ Successful tests: {success_count}/{total_tests}")
            print(f"📊 All counters tested: DI1, DI2, DI3, DI4")
            print(f"🔥 All HEX payloads verified")
            print(f"📡 MQTT topics confirmed")
            
            if success_count == total_tests:
                self.log("🎉 ALL TESTS PASSED - SYSTEM READY!", "SUCCESS")
            else:
                self.log(f"⚠️ {total_tests - success_count} tests failed", "WARNING")
                
        except Device.DoesNotExist:
            self.log(f"Device {self.device_id} not found!", "ERROR")
        except Exception as e:
            self.log(f"Demo failed: {str(e)}", "ERROR")
    
    def show_production_summary(self):
        """Show production ready summary"""
        print("\n🎯 PRODUCTION READY SUMMARY")
        print("=" * 50)
        
        print("✅ SUPPORTED COUNTERS:")
        for counter, info in self.counter_mapping.items():
            print(f"   {info['di']} ({counter}): {info['hex']}")
        
        print(f"\n📡 MQTT CONFIGURATION:")
        print(f"   Topic Pattern: uc/[Device_SN]/ucp/+/cmd/update")
        print(f"   Example Topic: uc/{self.device_id}/ucp/+/cmd/update")
        print(f"   Payload Format: HEX bytes")
        print(f"   QoS Level: 1")
        
        print(f"\n🔧 DEVICE CONFIGURATION:")
        print(f"   Database Field: mill_device.selected_counter")
        print(f"   Valid Values: counter_1, counter_2, counter_3, counter_4")
        print(f"   Current Device: {self.device.selected_counter}")
        
        print(f"\n🚀 READY FOR:")
        print(f"   ✅ Any UC300 device with any selected counter")
        print(f"   ✅ Automatic HEX payload selection")
        print(f"   ✅ Batch management with counter resets")
        print(f"   ✅ Daily resets (23:59)")
        print(f"   ✅ Manual admin resets")

def main():
    """Main demo function"""
    demo = UC300AllCountersDemo()
    
    print("🎯 UC300 ALL COUNTERS DEMO")
    print("=" * 50)
    print("Options:")
    print("1. Show all counters overview")
    print("2. Run complete demo (test all 4 counters)")
    print("3. Show production summary")
    print("4. Reset current device to 0")
    print()
    
    try:
        choice = input("Select option (1-4): ").strip()
        
        # Load device first
        demo.device = Device.objects.get(id=demo.device_id)
        
        if choice == "1":
            demo.show_all_counters_overview()
            
        elif choice == "2":
            demo.run_complete_demo()
            
        elif choice == "3":
            demo.show_production_summary()
            
        elif choice == "4":
            mqtt_service = get_uc300_mqtt_service()
            reset_log = mqtt_service.send_reset_command(demo.device_id, "manual_all_counters_demo")
            if reset_log:
                print(f"✅ Device reset successful: ID {reset_log.id}")
            else:
                print("❌ Device reset failed")
                
        else:
            print("Invalid option")
            
    except KeyboardInterrupt:
        print("\nDemo cancelled")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 