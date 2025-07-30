# 🔄 UC300 Counter Reset System - Implementatie Plan

## 📋 **OVERZICHT**

Implementatie van een UC300 counter reset systeem waarbij counters automatisch of handmatig gereset kunnen worden naar 0, waardoor productie berekeningen veel eenvoudiger en accurater worden.

## 🛡️ **HISTORISCHE DATA BESCHERMING - 100% GEGARANDEERD**

### Database Structuur Behouden:
```sql
-- BESTAANDE TABELLEN BLIJVEN INTACT
mqtt_data          -- Alle ruwe counter waardes (NOOIT VERWIJDERD)
mill_productiondata -- Alle berekende productie (NOOIT VERWIJDERD)

-- NIEUWE TABEL VOOR RESET TRACKING
counter_reset_log:
  - id
  - device_id  
  - reset_timestamp
  - counter_value_before_reset
  - reset_reason (daily/batch/manual)
  - created_at
```

### Data Continuïteit:
- **Voor Reset**: Alle historische data blijft bestaan
- **Na Reset**: Nieuwe data krijgt context via reset_log
- **Queries**: Kunnen data voor/na resets correct combineren

## 🔧 **IMPLEMENTATIE OPTIES**

### **Optie 1: Tijd-Gebaseerd Reset (Dagelijks)**
```yaml
Schedule: Elke dag om 06:00 (of gewenste tijd)
Voordelen:
  - Voorspelbaar patroon
  - Daily production = directe counter waarde
  - Eenvoudige rapportage
Nadelen:
  - Minder flexibel voor batches
```

### **Optie 2: Batch-Gebaseerd Reset**
```yaml
Trigger: Bij start van nieuwe batch
Voordelen:
  - Perfect voor batch tracking
  - Productie per batch = directe counter waarde
  - Flexibel timing
Nadelen:
  - Complexere scheduling
  - Handmatige interventie nodig
```

### **Optie 3: Hybride Systeem (AANBEVOLEN)**
```yaml
Implementatie:
  - Automatisch: Dagelijks om 06:00
  - Handmatig: Reset bij batch start
  - API: Voor programmatische controle
```

## 🚀 **IMPLEMENTATIE STAPPEN**

### **Fase 1: Database Uitbreiding**
```sql
-- Nieuwe tabel voor reset logging
CREATE TABLE counter_reset_log (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL,
    reset_timestamp TIMESTAMP NOT NULL,
    counter_1_before INTEGER,
    counter_2_before INTEGER, 
    counter_3_before INTEGER,
    counter_4_before INTEGER,
    reset_reason VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### **Fase 2: MQTT Command Service**
```python
class UC300CommandService:
    def reset_counter(self, device_id, counter_number=2):
        # Send MQTT command to UC300
        topic = f"uc/{device_id}/ucp/command/reset"
        payload = {"counter": counter_number, "value": 0}
        self.mqtt_client.publish(topic, json.dumps(payload))
    
    def reset_all_counters(self, device_id):
        # Reset all counters for device
        pass
    
    def schedule_daily_reset(self, device_id, time="06:00"):
        # Schedule automatic daily reset
        pass
```

### **Fase 3: Production Calculation Update**
```python
def calculate_production_with_resets(self, device_id, counter_value):
    # Check if reset occurred today
    reset_today = self.get_reset_log_today(device_id)
    
    if reset_today:
        # Production = current counter value (started from 0)
        return counter_value
    else:
        # Use existing logic for backward compatibility
        return self.calculate_daily_production_correctly(device_id, counter_value)
```

### **Fase 4: Web Interface**
```python
# Django Admin Interface
class CounterResetAdmin:
    def reset_device_counter(self, device_id):
        # Manual reset trigger
        pass
    
    def schedule_reset(self, device_id, schedule):
        # Schedule management
        pass
    
    def view_reset_history(self, device_id):
        # Historical reset tracking
        pass
```

## 📊 **VOOR/NA VERGELIJKING**

### **HUIDIG SYSTEEM:**
```
Day 1: Counter = 1000 → Daily = 1000 - 0 = 1000
Day 2: Counter = 1500 → Daily = 1500 - 1000 = 500
Gap (3 dagen geen data)
Day 6: Counter = 2000 → Daily = 2000 - 1500 = 500 ✅ (na onze fix)
```

### **RESET SYSTEEM:**
```
Day 1: Counter = 1000, Reset → Daily = 1000 ✅
Day 2: Counter = 500, Reset → Daily = 500 ✅  
Gap (3 dagen geen data)
Day 6: Counter = 600, Reset → Daily = 600 ✅
```

## 🔒 **VEILIGHEID & BACKUP**

### **Data Veiligheid:**
1. **Database Backup**: Voor elke reset
2. **Reset Logging**: Alle resets gelogd
3. **Rollback Mogelijkheid**: Via reset_log
4. **Validation**: Counter waarde checks voor reset

### **Fail-Safe Mechanismen:**
```python
def safe_reset_counter(self, device_id):
    # 1. Backup current state
    backup = self.create_backup(device_id)
    
    # 2. Log reset intent
    reset_log = self.log_reset_intent(device_id)
    
    # 3. Send reset command
    success = self.send_reset_command(device_id)
    
    # 4. Verify reset occurred
    if not self.verify_reset(device_id):
        self.rollback(backup)
        raise ResetFailedException()
    
    # 5. Confirm in log
    self.confirm_reset_success(reset_log)
```

## ⚡ **IMPLEMENTATIE EFFORT**

### **Werk Inschatting:**
```
Fase 1 (Database): 4-6 uur
Fase 2 (MQTT Commands): 8-12 uur  
Fase 3 (Production Logic): 6-8 uur
Fase 4 (Web Interface): 6-10 uur
Testing & Deployment: 8-12 uur

TOTAAL: 32-48 uur (4-6 werkdagen)
```

### **Risico Assessment:**
- **Laag Risico**: Database uitbreiding
- **Medium Risiko**: MQTT command implementatie  
- **Laag Risico**: Production logic update
- **Zeer Laag Risico**: Data verlies (door backup systeem)

## 🎯 **AANBEVELING**

### **JA, IMPLEMENT HET RESET SYSTEEM!**

**Redenen:**
1. **Veel eenvoudiger** dan huidige gap handling
2. **Accurater** productie tracking  
3. **Perfecte batch** tracking mogelijkheid
4. **Historische data** 100% veilig
5. **Toekomstbestendig** systeem
6. **Relatief weinig werk** (4-6 dagen)

### **Start Strategie:**
1. **Pilot**: Test met 1-2 devices eerst
2. **Parallel**: Laat huidig systeem doorlopen
3. **Gradueel**: Migreer device per device
4. **Monitor**: Vergelijk resultaten 2-4 weken

**Dit systeem lost al jouw problemen op EN maakt de toekomst veel makkelijker! 🚀** 