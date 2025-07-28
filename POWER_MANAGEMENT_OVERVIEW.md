# Power Management Overview

## Nieuwe Super Admin Functionaliteit

### 1. Alle Devices Zonder Stroom (`/all-devices-without-power/`)

**Doel:** Centrale pagina voor super admins om alle devices zonder stroom te monitoren.

**Features:**
- Overzicht van alle devices zonder stroom
- Onderscheid tussen **Critical** (met counter activiteit) en **Warning** (alleen geen stroom)
- Real-time statistieken:
  - Total devices zonder stroom
  - Critical devices (met counter activiteit)
  - Warning devices (alleen geen stroom)
  - Total productie zonder stroom
- Auto-refresh elke 30 seconden
- Directe links naar gedetailleerde device analyse

**Toegang:** Alleen super admins

---

### 2. Device Gedetailleerde Power Analyse (`/device-detailed-analysis/<device_id>/`)

**Doel:** Uitgebreide analyse van één specifiek device.

**Features:**
- **Power Incidenten Analyse:**
  - Alle power loss incidenten van de laatste 7 dagen
  - Counter activiteit tijdens power loss
  - Productie zonder stroom berekening
  - Incident duur en timing

- **Real-time Statistieken:**
  - Total incidenten
  - Incidenten met counter activiteit
  - Total productie zonder stroom
  - Total downtime

- **Gedetailleerde Incident Weergave:**
  - Start/eind tijd
  - Counter waarden (start/eind)
  - Productie zonder stroom per incident
  - Counter veranderingen tijdens incident

- **Recent Power Events:**
  - Laatste 10 power events
  - Event type en severity
  - Resolved status

**Toegang:** Alleen super admins

---

## Navigatie

### Van Power Dashboard
- Super admins zien een rode knop "Alle Devices Zonder Stroom" in de header
- Directe toegang tot centrale monitoring

### Van Factory Power Overview
- "Details" knop bij elk device leidt naar gedetailleerde analyse
- Vervangt de oude device offline status pagina

---

## Business Logic

### Power Incident Detectie
1. **Power Loss Start:** Device heeft geen stroom (AIN1 = 0)
2. **Counter Activiteit Check:** Wordt counter waarde verhoogd tijdens power loss?
3. **Incident Classificatie:**
   - **Critical:** Power loss + counter activiteit = verdachte activiteit
   - **Warning:** Power loss zonder counter activiteit = normale offline status

### Productie Zonder Stroom Berekening
```
Productie zonder stroom = Eind counter - Start counter
```
- Alleen berekend als er daadwerkelijk counter activiteit is
- Toont exacte hoeveelheid productie tijdens power loss

### Incident Duur
- Incidenten korter dan 10 minuten worden gefilterd (normale power dips)
- Alleen significante incidenten worden getoond

---

## Verwijderde Functionaliteit

### Oude Device Offline Status
- **Verwijderd:** `device_offline_status` view
- **Verwijderd:** `device_offline_status.html` template
- **Verwijderd:** URL pattern `device-offline-status/`
- **Vervangen door:** `device_detailed_power_analysis`

**Reden:** De nieuwe functionaliteit is uitgebreider en biedt betere inzichten.

---

## URL Structure

### Nieuwe URLs
```
/all-devices-without-power/                    # Super admin overzicht
/device-detailed-analysis/<device_id>/        # Device specifieke analyse
```

### Behouden URLs
```
/power-dashboard/                             # Hoofd dashboard
/device-suspicious-activity/<device_id>/      # Suspicious activity analyse
/factory/<id>/power-overview/                 # Factory overzicht
```

---

## Service Methods

### UnifiedPowerManagementService

#### `get_all_devices_without_power()`
- Haalt alle devices zonder stroom op
- Sorteert op severity (critical eerst)
- Voegt gedetailleerde analyse toe per device

#### `get_device_detailed_power_analysis(device)`
- Analyseert power incidenten van laatste 7 dagen
- Berekent productie zonder stroom
- Toont counter activiteit tijdens power loss
- Levert uitgebreide statistieken

---

## Template Files

### Nieuwe Templates
- `all_devices_without_power.html` - Super admin overzicht
- `device_detailed_power_analysis.html` - Device analyse

### Aangepaste Templates
- `power_dashboard.html` - Toegevoegde super admin knop
- `factory_power_overview.html` - Updated "Details" knop

---

## Gebruik

### Voor Super Admins
1. Ga naar Power Dashboard
2. Klik op "Alle Devices Zonder Stroom" knop
3. Bekijk overzicht van alle problematische devices
4. Klik op "Details" voor uitgebreide analyse per device

### Voor Factory Managers
1. Ga naar Factory Power Overview
2. Klik op "Details" bij specifiek device
3. Bekijk gedetailleerde power analyse voor dat device

---

## Auto-refresh
- Alle pagina's refresh automatisch elke 30 seconden
- Real-time monitoring van power status
- Automatische updates van incidenten en statistieken

---

## Permissions
- **Super Admin:** Volledige toegang tot alle functionaliteit
- **Factory Managers:** Alleen toegang tot hun eigen factory devices
- **Normale Users:** Geen toegang tot power management

---

## Troubleshooting

### 404 Errors
- Zorg dat Docker containers zijn gerebuild na code changes
- Check URL patterns in `mill/urls.py`
- Verifieer view imports in `power_management_views.py`

### Geen Data
- Check of devices daadwerkelijk data genereren
- Verifieer RawData records voor de laatste 7 dagen
- Controleer DevicePowerStatus records

### Performance
- Analyse beperkt tot laatste 7 dagen voor performance
- Auto-refresh elke 30 seconden voor real-time updates
- Paginering voor grote datasets 