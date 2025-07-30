#!/usr/bin/env python3
"""
🔄 UC300 Counter Reset System - Praktijk Demo

Dit script demonstreert hoe het UC300 reset systeem zou werken
en waarom het veel beter is dan het huidige systeem.
"""

from datetime import datetime, timedelta
import json

class UC300ResetSystemDemo:
    
    def __init__(self):
        # Simuleer database state
        self.mqtt_data = []
        self.production_data = []
        self.reset_log = []
        self.current_time = datetime(2024, 1, 1, 6, 0, 0)  # Start 1 jan 06:00
        
    def log(self, message, level="INFO"):
        print(f"[{self.current_time.strftime('%Y-%m-%d %H:%M')}] {level}: {message}")
    
    def simulate_counter_data(self, device_id, counter_value):
        """Simuleer ontvangen MQTT data van UC300"""
        self.mqtt_data.append({
            'device_id': device_id,
            'timestamp': self.current_time,
            'counter_2': counter_value
        })
        self.log(f"📡 MQTT Data: Device {device_id} - Counter: {counter_value}")
    
    def reset_counter(self, device_id, reason="daily"):
        """Reset UC300 counter via MQTT command"""
        # Haal huidige counter waarde
        current_data = [d for d in self.mqtt_data if d['device_id'] == device_id]
        if current_data:
            last_value = current_data[-1]['counter_2']
        else:
            last_value = 0
            
        # Log reset VOOR het uitvoeren
        reset_entry = {
            'device_id': device_id,
            'reset_timestamp': self.current_time,
            'counter_2_before': last_value,
            'reset_reason': reason
        }
        self.reset_log.append(reset_entry)
        
        # Simuleer MQTT command naar UC300
        self.log(f"🔄 SENDING RESET: Device {device_id} - Counter was: {last_value}")
        
        # UC300 reset counter naar 0 (volgende data wordt vanaf 0)
        self.log(f"✅ RESET SUCCESS: Device {device_id} - Counter now: 0")
        
        return True
    
    def calculate_production_with_reset(self, device_id, current_counter):
        """Nieuwe productie berekening met reset systeem"""
        # Check of er vandaag een reset was
        today_start = self.current_time.replace(hour=0, minute=0, second=0)
        today_end = self.current_time.replace(hour=23, minute=59, second=59)
        
        reset_today = [r for r in self.reset_log 
                      if r['device_id'] == device_id 
                      and today_start <= r['reset_timestamp'] <= today_end]
        
        if reset_today:
            # Er was reset vandaag - productie = current counter (started from 0)
            daily_production = current_counter
            self.log(f"💡 RESET METHOD: Daily = {current_counter} (direct counter waarde)")
        else:
            # Geen reset - gebruik oude methode voor backward compatibility
            yesterday_data = [d for d in self.mqtt_data 
                            if d['device_id'] == device_id 
                            and d['timestamp'].date() == (self.current_time.date() - timedelta(days=1))]
            
            if yesterday_data:
                yesterday_value = yesterday_data[-1]['counter_2']
                daily_production = max(0, current_counter - yesterday_value)
                self.log(f"💡 DIFF METHOD: Daily = {current_counter} - {yesterday_value} = {daily_production}")
            else:
                daily_production = current_counter
                self.log(f"💡 NEW DEVICE: Daily = {current_counter}")
        
        # Sla productie data op
        self.production_data.append({
            'device_id': device_id,
            'date': self.current_time.date(),
            'daily_production': daily_production,
            'timestamp': self.current_time
        })
        
        return daily_production
    
    def advance_time(self, hours=0, days=0):
        """Advance simulatie tijd"""
        self.current_time += timedelta(hours=hours, days=days)
    
    def run_scenario(self):
        """Demonstreer reset systeem scenario"""
        
        print("🏭 UC300 RESET SYSTEM DEMONSTRATION")
        print("=" * 60)
        print()
        
        device_id = "6445E27562470013"
        
        # === DAG 1: Normale productie ===
        print("📅 DAG 1: Normale Werkdag")
        print("-" * 30)
        
        # 06:00 - Daily reset
        self.reset_counter(device_id, "daily")
        
        # 08:00 - Werk start, counter begint te tellen
        self.advance_time(hours=2)
        self.simulate_counter_data(device_id, 150)  # 150 eenheden geproduceerd
        
        # 17:00 - Einde werkdag
        self.advance_time(hours=9) 
        self.simulate_counter_data(device_id, 800)  # Totaal 800 eenheden
        
        daily_prod = self.calculate_production_with_reset(device_id, 800)
        print(f"🎯 RESULTAAT DAG 1: Daily Production = {daily_prod}")
        print()
        
        # === DAG 2: Normale productie ===
        print("📅 DAG 2: Normale Werkdag")
        print("-" * 30)
        
        self.advance_time(days=1, hours=-9)  # Next day 06:00
        self.reset_counter(device_id, "daily")
        
        self.advance_time(hours=11)  # 17:00
        self.simulate_counter_data(device_id, 600)  # 600 eenheden
        
        daily_prod = self.calculate_production_with_reset(device_id, 600)
        print(f"🎯 RESULTAAT DAG 2: Daily Production = {daily_prod}")
        print()
        
        # === DAG 3-5: Weekend + storing (geen data) ===
        print("📅 DAG 3-5: Weekend + Storing (Geen Data)")
        print("-" * 30)
        
        for day in [3, 4, 5]:
            self.advance_time(days=1, hours=-11)  # Next day 06:00
            # Reset wordt wel uitgevoerd, maar geen productie data
            self.reset_counter(device_id, "daily")
            print(f"Day {day}: Reset uitgevoerd, maar geen productie data")
        print()
        
        # === DAG 6: Terug aan het werk ===
        print("📅 DAG 6: Terug Aan Het Werk Na Gap")
        print("-" * 30)
        
        self.advance_time(days=1, hours=0)  # Day 6, 06:00
        self.reset_counter(device_id, "daily")
        
        self.advance_time(hours=11)  # 17:00
        self.simulate_counter_data(device_id, 750)  # 750 eenheden
        
        daily_prod = self.calculate_production_with_reset(device_id, 750)
        print(f"🎯 RESULTAAT DAG 6: Daily Production = {daily_prod}")
        print()
        
        # === BATCH RESET DEMO ===
        print("📅 BATCH RESET DEMONSTRATION")
        print("-" * 30)
        
        # Batch 1 start
        self.advance_time(hours=1)
        self.reset_counter(device_id, "batch_start")
        self.advance_time(hours=3)
        self.simulate_counter_data(device_id, 400)
        batch1_prod = self.calculate_production_with_reset(device_id, 400)
        print(f"🎯 BATCH 1: Production = {batch1_prod}")
        
        # Batch 2 start  
        self.advance_time(hours=1)
        self.reset_counter(device_id, "batch_start")
        self.advance_time(hours=2)
        self.simulate_counter_data(device_id, 300)
        batch2_prod = self.calculate_production_with_reset(device_id, 300)
        print(f"🎯 BATCH 2: Production = {batch2_prod}")
        print()
        
        # === RESULTATEN SAMENVATTING ===
        self.show_summary()
    
    def show_summary(self):
        """Toon samenvatting van resultaten"""
        print("📊 SAMENVATTING RESULTATEN")
        print("=" * 60)
        
        print("\n🔄 RESET LOG:")
        for reset in self.reset_log:
            print(f"  {reset['reset_timestamp'].strftime('%Y-%m-%d %H:%M')} - "
                  f"Device: {reset['device_id']} - "
                  f"Reason: {reset['reset_reason']} - "
                  f"Counter was: {reset['counter_2_before']}")
        
        print("\n📈 PRODUCTION DATA:")
        for prod in self.production_data:
            print(f"  {prod['date']} - "
                  f"Device: {prod['device_id']} - "
                  f"Daily: {prod['daily_production']}")
        
        print("\n✅ VOORDELEN RESET SYSTEEM:")
        print("• Geen complexe gap calculations")
        print("• Daily production = directe counter waarde")
        print("• Perfect voor batch tracking")
        print("• Geen artificiële spikes mogelijk")
        print("• Historische data 100% veilig")
        print("• Eenvoudige troubleshooting")
        print()
        
        print("💪 CONCLUSIE:")
        print("Het reset systeem is veel eenvoudiger, accurater en flexibeler!")
        print("Implementatie is zeer haalbaar en lost alle huidige problemen op!")

def main():
    """Run de UC300 reset system demonstratie"""
    demo = UC300ResetSystemDemo()
    demo.run_scenario()

if __name__ == "__main__":
    main() 