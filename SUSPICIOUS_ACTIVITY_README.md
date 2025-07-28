# Suspicious Activity Detection - Power Management

## Overview

Deze nieuwe functionaliteit detecteert verdachte activiteit wanneer er geen stroom is maar de counter wel blijft lopen. Dit is een kritieke beveiligingsfunctie die helpt bij het identificeren van mogelijke systeemproblemen of onregelmatigheden.

## Hoe het werkt

### Logica
1. **Power Loss Detection**: Het systeem detecteert wanneer een device geen stroom heeft (AIN1 value ≤ 0)
2. **5-Minute Check**: Na 5 minuten (configureerbaar) wordt opnieuw gecontroleerd
3. **Production Analysis**: Het systeem vergelijkt de counter waarden tussen de eerste power loss en de check time
4. **Suspicious Activity Detection**: 
   - Als er productie is tijdens de no-power periode → **VERDACHT** (kritiek probleem)
   - Als er geen productie is → **NORMAAL** (factory is offline)

### Scenario's

#### Scenario 1: Verdachte Activiteit (CRITICAL)
```
Tijd 0: Power loss detected (counter_1 = 1000)
Tijd 5 min: Still no power, but counter_1 = 1050
Resultaat: 50 bags produced without power → SUSPICIOUS ACTIVITY
```

#### Scenario 2: Normale Offline Status (NORMAL)
```
Tijd 0: Power loss detected (counter_1 = 1000)
Tijd 5 min: Still no power, counter_1 = 1000
Resultaat: No production during no-power period → NORMAL (factory offline)
```

## Functionaliteit

### 1. Web Interface

#### Device Power Status Page
- Nieuwe knop: "Suspicious Activity Analysis"
- Toegankelijk via: `/device-power-status/<device_id>/`
- Klik op "Suspicious Activity Analysis" knop

#### Suspicious Activity Analysis Page
- URL: `/device-suspicious-activity/<device_id>/`
- Toont gedetailleerde analyse van verdachte activiteit
- Configureerbare check interval (1, 3, 5, 10, 15 minuten)
- Real-time status updates

#### Factory Power Overview
- Nieuwe knop: "Suspicious" naast elke device
- Snelle toegang tot suspicious activity analysis

### 2. Management Command

```bash
# Check alle devices met 5-minuten interval
python manage.py check_suspicious_activity

# Check specifieke device
python manage.py check_suspicious_activity --device-id DEVICE_ID

# Check devices in specifieke factory
python manage.py check_suspicious_activity --factory-id FACTORY_ID

# Check met aangepaste interval
python manage.py check_suspicious_activity --check-interval 10

# Maak power events aan voor verdachte activiteit
python manage.py check_suspicious_activity --create-events
```

### 3. API Endpoints

#### Suspicious Activity Analysis
- **URL**: `/device-suspicious-activity/<device_id>/`
- **Method**: GET
- **Parameters**: 
  - `check_interval`: Check interval in minuten (default: 5)
- **Response**: JSON met analysis data

## Technische Implementatie

### Models
- `DevicePowerStatus`: Houdt power status bij
- `PowerEvent`: Registreert verdachte activiteit events
- `RawData`: Counter en power data

### Services
- `UnifiedPowerManagementService.get_suspicious_activity_analysis()`: Hoofdlogica
- `PowerManagementService.get_suspicious_activity_analysis()`: Alternatieve implementatie

### Views
- `device_suspicious_activity()`: Web interface
- URL routing in `mill/urls.py`

### Templates
- `device_suspicious_activity.html`: Analysis pagina
- Updates in `device_power_status.html` en `factory_power_overview.html`

## Configuratie

### Check Interval
Standaard: 5 minuten
Configureerbaar via:
- Web interface dropdown
- Management command parameter
- URL parameter

### Permissions
- Alleen beschikbaar voor super administrators
- Vereist power management permissions

## Monitoring en Notificaties

### Automatic Checks
- Management command kan geautomatiseerd worden via cron
- Aanbevolen: Elke 5-10 minuten uitvoeren

### Notifications
- Power events worden aangemaakt voor verdachte activiteit
- Email notificaties naar verantwoordelijke gebruikers
- In-app notificaties

### Logging
- Alle checks worden gelogd
- Errors worden geregistreerd in Django logs
- Management command output voor debugging

## Troubleshooting

### Veelvoorkomende Problemen

1. **"No power status data available"**
   - Device heeft geen DevicePowerStatus record
   - Run: `python manage.py update_power_status_from_database`

2. **"No power loss time recorded"**
   - Device heeft momenteel power
   - Wacht tot power loss optreedt

3. **"No data available for analysis period"**
   - Geen RawData records in de analyse periode
   - Controleer data sync status

### Debug Commands

```bash
# Check power status voor alle devices
python manage.py update_power_status_from_database

# Sync counter data
python manage.py sync_counter_data

# Test suspicious activity voor specifieke device
python manage.py check_suspicious_activity --device-id DEVICE_ID --create-events
```

## Security Considerations

### Data Privacy
- Alleen super administrators hebben toegang
- Power data wordt veilig opgeslagen
- Geen persoonlijke informatie in logs

### System Integrity
- Verdachte activiteit kan wijzen op:
  - Hardware problemen
  - Sensor falen
  - Data integriteit issues
  - Mogelijke sabotage

### Response Protocol
1. **Immediate**: Check device status
2. **Investigation**: Analyseer counter data
3. **Resolution**: Fix hardware/software issues
4. **Documentation**: Log incident en oplossing

## Future Enhancements

### Geplande Verbeteringen
1. **Machine Learning**: Automatische anomalie detectie
2. **Predictive Analytics**: Voorspellen van power issues
3. **Advanced Notifications**: SMS, Slack, Teams integratie
4. **Historical Analysis**: Trend analysis over tijd
5. **Device Groups**: Bulk analysis voor factory groups

### API Extensions
- REST API voor externe systemen
- Webhook support voor real-time alerts
- GraphQL interface voor complexe queries

## Support

Voor vragen of problemen:
1. Check Django logs voor errors
2. Run management commands voor debugging
3. Controleer device power status
4. Verify data sync status
5. Contact system administrator 