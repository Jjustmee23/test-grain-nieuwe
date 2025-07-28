# Device Offline Status - Power Management

## Overview

Deze nieuwe functionaliteit toont gedetailleerde informatie over hoe lang een device offline is geweest zonder counter activiteit, of hoe lang het heeft gedraaid zonder stroom maar met counter activiteit. Dit geeft een duidelijk overzicht van de device status en helpt bij het identificeren van problemen.

## Functionaliteit

### Wat het toont:

1. **Current Status**: Huidige status van het device
   - **ONLINE**: Device heeft stroom en werkt normaal
   - **NO POWER + COUNTER**: Device heeft geen stroom maar counter is actief (kritiek)
   - **OFFLINE**: Device heeft geen stroom en geen counter activiteit (normaal)

2. **Offline Statistics** (laatste 24 uur):
   - **No Power + Counter Activity**: Tijd dat device draaide zonder stroom maar met counter
   - **No Power + No Counter**: Tijd dat device offline was zonder counter activiteit
   - **Total Offline Time**: Totale tijd dat device offline was
   - **Offline Periods**: Aantal offline periodes

3. **Offline Periods**: Gedetailleerde lijst van alle offline periodes in de laatste 24 uur
   - Start en eind tijd
   - Duur van elke periode
   - Type offline status
   - Counter activiteit tijdens offline periode

4. **Recommendations**: Automatische aanbevelingen gebaseerd op de analyse

## Toegang

### Via Factory Power Overview:
1. Ga naar `/factory/<factory_id>/power-overview/`
2. Klik op de "Details" knop naast een device
3. Je wordt doorgestuurd naar de Device Offline Status pagina

### Directe URL:
- `/device-offline-status/<device_id>/`

## Status Types

### 🟢 ONLINE
```
Device heeft stroom (AIN1 > 0)
Counter activiteit: Normaal
Status: Geen probleem
```

### 🔴 NO POWER + COUNTER (CRITICAL)
```
Device heeft geen stroom (AIN1 = 0)
Counter activiteit: JA
Status: KRITIEK PROBLEEM
```
**Dit betekent dat het device draait zonder stroom - dit is verdacht en vereist onmiddellijke aandacht!**

### 🟡 OFFLINE (NORMAL)
```
Device heeft geen stroom (AIN1 = 0)
Counter activiteit: NEE
Status: Normaal (factory offline)
```
**Dit is normaal - de factory is gewoon offline en er is geen productie.**

## Interface Features

### Real-time Updates
- Pagina vernieuwt automatisch elke 30 seconden
- Toont live status van het device

### Visual Indicators
- **Rode badges**: Kritieke problemen (no power + counter)
- **Gele badges**: Waarschuwingen (offline)
- **Groene badges**: Normale status (online)

### Time Display
- Duidelijke tijdweergave in HH:MM:SS formaat
- Power loss tijd en offline duur
- Gedetailleerde periode informatie

### Action Buttons
- **Back to Dashboard**: Terug naar power dashboard
- **Suspicious Activity Analysis**: Ga naar verdachte activiteit analyse
- **View Power Events**: Bekijk alle power events voor dit device

## Technische Details

### Data Analysis
- Analyseert laatste 24 uur van RawData
- Vergelijkt AIN1 waarden (power) met counter activiteit
- Identificeert offline periodes en hun types

### Performance
- Efficiënte database queries
- Caching van resultaten
- Automatische refresh voor real-time updates

### Error Handling
- Graceful handling van ontbrekende data
- Duidelijke foutmeldingen
- Fallback naar basis status informatie

## Use Cases

### Scenario 1: Normale Offline Status
```
Device: _نور_السبطين_1
Status: OFFLINE
Power: 0.00 kW
Counter: Geen activiteit
Resultaat: Factory is offline (normaal)
```

### Scenario 2: Kritiek Probleem
```
Device: _نور_السبطين_1
Status: NO POWER + COUNTER
Power: 0.00 kW
Counter: Actief
Resultaat: Device draait zonder stroom (kritiek)
```

### Scenario 3: Online Status
```
Device: _نور_السبطين_2
Status: ONLINE
Power: 1.60 kW
Counter: Normale activiteit
Resultaat: Device werkt normaal
```

## Recommendations

### Automatische Aanbevelingen
Het systeem genereert automatisch aanbevelingen gebaseerd op de analyse:

1. **Critical**: Device draait zonder stroom
   - Controleer hardware
   - Onderzoek mogelijke sabotage
   - Check sensor status

2. **Warning**: Langdurige offline periodes
   - Controleer power supply
   - Verify network connectivity
   - Check device health

3. **Info**: Normale offline status
   - Factory is offline (geen actie nodig)
   - Monitor voor herstel

## Integration

### Met Bestaande Systeem
- Integreert met power management systeem
- Gebruikt bestaande DevicePowerStatus en RawData models
- Compatibel met suspicious activity detection

### Permissions
- Alleen beschikbaar voor super administrators
- Vereist power management permissions
- Beveiligde toegang via Django authentication

## Troubleshooting

### Veelvoorkomende Problemen

1. **"No data available"**
   - Controleer of er RawData records zijn
   - Verify device connectivity
   - Check data sync status

2. **"No power status data"**
   - Run: `python manage.py update_power_status_from_database`
   - Controleer DevicePowerStatus records

3. **Incorrecte tijden**
   - Verify timezone settings
   - Check server tijd synchronisatie

### Debug Commands
```bash
# Check power status
python manage.py update_power_status_from_database

# Sync counter data
python manage.py sync_counter_data

# Check specific device
python manage.py check_suspicious_activity --device-id DEVICE_ID
```

## Future Enhancements

### Geplande Verbeteringen
1. **Historical Analysis**: Trend analysis over langere periodes
2. **Predictive Alerts**: Voorspellen van offline periodes
3. **Export Functionality**: Export data naar CSV/Excel
4. **Email Notifications**: Automatische alerts voor kritieke status
5. **Mobile Support**: Responsive design voor mobiele apparaten

### API Extensions
- REST API endpoints voor externe systemen
- Webhook support voor real-time status updates
- GraphQL interface voor complexe queries

## Support

Voor vragen of problemen:
1. Check Django logs voor errors
2. Verify device connectivity
3. Controleer power status data
4. Run debug commands
5. Contact system administrator

## Docker Deployment

De functionaliteit is beschikbaar in de Docker container:
```bash
# Build en start containers
docker-compose build
docker-compose up -d

# Access via
http://localhost:8000/device-offline-status/<device_id>/
``` 