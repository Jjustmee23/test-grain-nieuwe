# Batch System Documentation

## Overzicht

Het batch systeem is het hart van de Mill Management applicatie en beheert de volledige productiecyclus van tarwe tot meel. Dit document beschrijft de architectuur, functionaliteiten en best practices voor het batch systeem.

## Systeem Architectuur

### Core Components

1. **Batch Model** (`mill/models.py`)
   - Centraal model voor batch beheer
   - Bevat productie parameters, status tracking, en workflow management
   - Automatische berekeningen voor verwachte output

2. **BatchProductionService** (`mill/services/batch_production_service.py`)
   - Centrale service voor productie berekeningen
   - Integreert RawData en ProductionData bronnen
   - Converteert counter units naar tonnage

3. **BatchNotificationService** (`mill/services/batch_notification_service.py`)
   - Beheert notificaties voor batch gebeurtenissen
   - Ondersteunt email en in-app notificaties
   - Integreert met gebruiker voorkeuren

4. **Batch Views** (`mill/views/batch_views.py`)
   - CRUD operaties voor batches
   - Workflow management (approve, start, stop)
   - API endpoints voor AJAX operations

## Batch Workflow

### Status Overgangen

```
pending → approved → in_process → completed/stopped
   ↓         ↓           ↓
rejected  rejected    paused → in_process
```

#### Status Beschrijvingen

- **pending**: Nieuwe batch wacht op goedkeuring
- **approved**: Batch is goedgekeurd en kan gestart worden
- **in_process**: Productie is actief
- **paused**: Productie is tijdelijk gestopt
- **completed**: Batch is succesvol afgerond
- **stopped**: Batch is geforceerd gestopt
- **rejected**: Batch is afgewezen

### Permissions & Autorisatie

- **Factory Responsible Users**: Kunnen batches goedkeuren en starten voor hun fabrieken
- **Super Admins**: Volledige controle over alle batch operaties
- **Admins**: Kunnen batches bekijken en beperkte operaties uitvoeren

## Productie Berekeningen

### Conversie Factoren

```python
CONVERSION_FACTOR = 50.0  # kg per counter unit
TONS_PER_KG = 1000.0     # 1000 kg = 1 ton
```

### Formules

**Verwachte Output**:
```
expected_output = wheat_amount * ((100 - waste_factor) / 100)
```

**Werkelijke Output**:
```
production_units = current_value - start_value
actual_output = (production_units * CONVERSION_FACTOR) / TONS_PER_KG
```

**Voortgang Percentage**:
```
progress = (actual_output / expected_output) * 100
```

## Data Bronnen

### Prioriteit van Data Bronnen

1. **RawData** (Primair)
   - Direct van MQTT/device counters
   - Meest accurate real-time data
   - Gebruikt voor realtime tracking

2. **ProductionData** (Fallback)
   - Geaggregeerde dagelijkse productie
   - Gebruikt wanneer RawData niet beschikbaar is

### Database Optimalisaties

- `select_related()` voor factory, city, approved_by relaties
- `prefetch_related()` voor devices, notifications, flour_bag_counts
- Database locking met `select_for_update()` voor status wijzigingen

## API Endpoints

### Batch Management

- `POST /batches/<id>/approve/` - Batch goedkeuren
- `POST /batches/<id>/start/` - Batch starten
- `POST /batches/<id>/stop/` - Batch stoppen
- `POST /batches/<id>/auto-update/` - Automatische update van productie data
- `POST /batches/<id>/manage/` - Super admin management acties

### Bulk Operations

- `POST /batches/bulk-delete/` - Meerdere batches verwijderen (alleen super admin)

## Notificatie Systeem

### Notification Types

- `batch_created` - Nieuwe batch toegewezen
- `batch_approved` - Batch goedgekeurd
- `batch_started` - Productie gestart
- `batch_completed` - Batch voltooid
- `batch_100_percent` - 100% productie bereikt

### Email Integration

- Microsoft 365 OAuth2 integratie
- Template-based emails
- User preference management
- Delivery tracking

## Automatisering

### Management Commands

1. **auto_update_batches.py**
   ```bash
   python manage.py auto_update_batches [--dry-run] [--batch-id=X] [--factory-id=Y]
   ```
   - Update alle actieve batches met laatste productie data
   - Automatische completion bij 100% voortgang

2. **update_batches.py**
   ```bash
   python manage.py update_batches
   ```
   - Basis batch update functionaliteit

### Cron Job Aanbevelingen

```bash
# Update batches elke 5 minuten
*/5 * * * * /path/to/python /path/to/manage.py auto_update_batches

# Cleanup oude notificaties dagelijks
0 2 * * * /path/to/python /path/to/manage.py cleanup_old_notifications
```

## Error Handling

### Race Condition Prevention

- Database locking met `select_for_update()`
- Atomic transactions voor status wijzigingen
- Validation van status overgangen

### Logging

- Uitgebreide logging in BatchProductionService
- Error tracking voor data inconsistenties
- Warning logs voor onverwachte waardes

### Common Error Scenarios

1. **Negative Counter Values**
   - Automatische correctie naar 0
   - Warning log generatie
   - Graceful handling

2. **Missing Device Data**
   - Fallback naar ProductionData
   - Clear error messages
   - System continues operation

3. **Invalid Status Transitions**
   - Rejection met specifieke error message
   - State preservation
   - User feedback

## Security

### Input Validation

- Form validation in BatchForm
- Model-level validators
- API parameter validation

### CSRF Protection

- CSRF tokens in alle POST requests
- AJAX requests include CSRF headers

### SQL Injection Prevention

- Django ORM gebruik (geen raw SQL)
- Parameterized queries
- Input sanitization

## Performance Optimizations

### Database Queries

- Eager loading met select_related/prefetch_related
- Index optimization op frequent queries
- Batch operations voor bulk updates

### Caching Strategy

- Template fragment caching voor heavy computations
- Redis caching voor frequent data
- Browser caching voor static assets

## Testing

### Unit Tests

- BatchProductionService tests (`mill/tests/test_batch_production_service.py`)
- Model validation tests
- API endpoint tests

### Test Coverage Areas

- Conversion calculations
- Status transitions
- Permission checking
- Edge cases (zero values, negative numbers)
- Multiple device scenarios

### Running Tests

```bash
python manage.py test mill.tests.test_batch_production_service
```

## Best Practices

### Development

1. **Always use transactions** voor status wijzigingen
2. **Validate inputs** in services en views
3. **Log belangrijke events** voor debugging
4. **Test edge cases** zoals negatieve waardes
5. **Use type hints** voor better code documentation

### Production

1. **Monitor batch progress** via dashboards
2. **Set up alerts** voor stuck batches
3. **Regular backup** van batch data
4. **Performance monitoring** van heavy queries
5. **Capacity planning** voor concurrent batches

## Troubleshooting

### Common Issues

1. **Batch niet automatisch updating**
   - Check device connection
   - Verify RawData availability
   - Check management command execution

2. **Incorrect progress calculations**
   - Verify conversion factors
   - Check counter reset scenarios
   - Validate start/end values

3. **Permission errors**
   - Check user group membership
   - Verify factory assignments
   - Review responsible_users relations

### Debug Commands

```bash
# Check batch status
python manage.py shell -c "from mill.models import Batch; print(Batch.objects.filter(status='in_process').count())"

# Test batch calculation
python manage.py shell -c "
from mill.models import Batch
from mill.services.batch_production_service import BatchProductionService
service = BatchProductionService()
batch = Batch.objects.get(batch_number='YOUR_BATCH')
print(service.calculate_batch_progress(batch))
"

# Dry run batch updates
python manage.py auto_update_batches --dry-run
```

## Migration Guide

### Database Schema Changes

1. **Adding new fields**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Data migrations**
   - Create data migration files
   - Test on staging environment
   - Backup before production migration

### Version Compatibility

- Backwards compatibility maintained voor major fields
- Deprecation warnings voor obsolete features
- Migration scripts voor data transformation

## Future Enhancements

### Planned Features

1. **Real-time WebSocket updates**
2. **Advanced analytics dashboard**
3. **Mobile app integration**
4. **Machine learning predictions**
5. **IoT sensor integration**

### API Versioning

- REST API versioning strategy
- Backwards compatibility policy
- Documentation maintenance

---

*Last updated: January 2025*
*Version: 1.0*