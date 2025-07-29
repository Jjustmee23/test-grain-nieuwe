# Lokaal Testen van het Batch Systeem met Docker

## Voorbereiding

### 1. Zorg ervoor dat Docker Desktop draait
- Start Docker Desktop op je machine
- Controleer dat Docker correct werkt:
```bash
docker --version
docker-compose --version
```

### 2. Ga naar de project directory
```bash
cd /path/to/project-mill-application
```

## Docker Container Herbouwen

### Stap 1: Stop bestaande containers
```bash
# Stop alle draaiende containers
docker-compose down

# Verwijder containers, netwerken en volumes (optioneel)
docker-compose down -v --remove-orphans
```

### Stap 2: Verwijder oude images (optioneel)
```bash
# Bekijk bestaande images
docker images

# Verwijder oude mill application images
docker rmi project-mill-application-web
docker rmi project-mill-application-raw-data-sync

# Of verwijder alle ongebruikte images
docker system prune -a
```

### Stap 3: Rebuild de containers
```bash
# Rebuild alle services
docker-compose build --no-cache

# Of rebuild alleen de web service
docker-compose build --no-cache web
```

### Stap 4: Start de services
```bash
# Start alle services in detached mode
docker-compose up -d

# Of start met logs zichtbaar
docker-compose up
```

## Database Setup

### Wacht tot databases gereed zijn
```bash
# Check database status
docker-compose logs postgres
docker-compose logs counter-postgres

# Wacht tot je "database system is ready to accept connections" ziet
```

### Run migraties
```bash
# Run Django migraties
docker-compose exec web python manage.py migrate

# Maak superuser aan (optioneel)
docker-compose exec web python manage.py createsuperuser
```

## Batch Systeem Testen

### 1. Test de Batch Production Service

#### Unit Tests Draaien
```bash
# Run de nieuwe unit tests
docker-compose exec web python manage.py test mill.tests.test_batch_production_service

# Run alle tests
docker-compose exec web python manage.py test
```

#### Manual Service Test
```bash
# Open Django shell
docker-compose exec web python manage.py shell

# Test BatchProductionService
from mill.services.batch_production_service import BatchProductionService
from mill.models import Batch, Factory, Device, City
from decimal import Decimal

# Check conversion factor
service = BatchProductionService()
print(f"Conversion factor: {service.CONVERSION_FACTOR} kg/unit")

# Test met een bestaande batch (als die er is)
batches = Batch.objects.all()
if batches.exists():
    batch = batches.first()
    result = service.calculate_batch_progress(batch)
    print(f"Batch progress result: {result}")
```

### 2. Test Data Aanmaken

#### Basis Test Data
```bash
docker-compose exec web python manage.py shell
```

```python
# Maak test data aan
from mill.models import City, Factory, Device, Batch, ProductionData
from decimal import Decimal
from django.contrib.auth.models import User

# Maak test city
city = City.objects.get_or_create(name="Test City", defaults={'status': True})[0]

# Maak test factory
factory = Factory.objects.get_or_create(
    name="Test Factory",
    defaults={'city': city, 'status': True, 'group': 'government'}
)[0]

# Maak test device
device = Device.objects.get_or_create(
    id="TEST_DEVICE_001",
    defaults={
        'name': "Test Device",
        'factory': factory,
        'status': True,
        'selected_counter': 'counter_1'
    }
)[0]

# Maak test batch
batch = Batch.objects.get_or_create(
    batch_number="TEST_BATCH_001",
    defaults={
        'factory': factory,
        'wheat_amount': Decimal('100.0'),
        'waste_factor': Decimal('20.0'),
        'expected_flour_output': Decimal('80.0'),
        'status': 'in_process'
    }
)[0]

# Maak productie data
production = ProductionData.objects.get_or_create(
    device=device,
    defaults={
        'daily_production': 800,  # 800 units = 40 tons
        'weekly_production': 5600,
        'monthly_production': 24000,
        'yearly_production': 288000
    }
)[0]

print(f"Test data created:")
print(f"City: {city.name}")
print(f"Factory: {factory.name}")
print(f"Device: {device.name}")
print(f"Batch: {batch.batch_number}")
print(f"Production: {production.daily_production} units")
```

### 3. Test Web Interface

#### Toegang tot de applicatie
```bash
# Applicatie is beschikbaar op:
http://localhost:8000

# Admin interface:
http://localhost:8000/admin/
```

#### Test Batch Functionaliteit
1. **Login**: Gebruik superuser account
2. **Ga naar Batches**: `/batches/`
3. **Test Batch List**: Controleer of data correct wordt getoond
4. **Test Batch Detail**: Klik op een batch om details te zien
5. **Test Batch Creatie**: Maak een nieuwe batch aan
6. **Test Status Updates**: Probeer batch status te wijzigen

### 4. Test Management Commands

#### Auto Update Batches
```bash
# Dry run test
docker-compose exec web python manage.py auto_update_batches --dry-run

# Echte update
docker-compose exec web python manage.py auto_update_batches

# Specifieke batch
docker-compose exec web python manage.py auto_update_batches --batch-id=1

# Specifieke factory
docker-compose exec web python manage.py auto_update_batches --factory-id=1
```

#### Andere Commands
```bash
# List factories
docker-compose exec web python manage.py list_factories

# Update power data
docker-compose exec web python manage.py auto_update_power_status

# Sync raw data
docker-compose exec web python manage.py sync_raw_data
```

### 5. Test API Endpoints

#### Met curl
```bash
# Get CSRF token eerst via browser of:
curl -c cookies.txt http://localhost:8000/admin/login/

# Test batch list API (als beschikbaar)
curl -b cookies.txt http://localhost:8000/api/batches/

# Test batch auto-update (na login)
curl -X POST -b cookies.txt \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  http://localhost:8000/batches/1/auto-update/
```

#### Met browser developer tools
1. Open browser developer tools (F12)
2. Ga naar Network tab
3. Test batch operations in de UI
4. Controleer API requests en responses

## Performance Testing

### Database Query Monitoring
```bash
# Django shell
docker-compose exec web python manage.py shell

# Test query optimalization
from django.db import connection
from mill.views.batch_views import BatchListView
from django.test import RequestFactory
from django.contrib.auth.models import User

# Maak test request
factory = RequestFactory()
request = factory.get('/batches/')
request.user = User.objects.first()

# Reset query count
connection.queries_log.clear()

# Test view
view = BatchListView()
view.request = request
queryset = view.get_queryset()
list(queryset)  # Force evaluation

# Check aantal queries
print(f"Number of queries: {len(connection.queries)}")
for query in connection.queries:
    print(f"Query: {query['sql'][:100]}...")
```

## Logging en Debugging

### Application Logs
```bash
# Bekijk logs van web container
docker-compose logs -f web

# Bekijk logs van specifieke service
docker-compose logs -f raw-data-sync

# Bekijk database logs
docker-compose logs postgres
```

### Django Debug Mode
Zorg ervoor dat `DEBUG=True` in je `.env` file staat voor lokaal testen.

### Error Tracking
```bash
# Bekijk Django logs binnen container
docker-compose exec web tail -f /app/logs/django.log

# Of check Python errors
docker-compose exec web python manage.py check
```

## Cleanup na Testen

### Stop services
```bash
# Stop containers maar behoud data
docker-compose down

# Stop en verwijder volumes (verliest data!)
docker-compose down -v
```

### Reset naar schone staat
```bash
# Verwijder alle containers en images
docker-compose down -v --remove-orphans
docker system prune -a

# Rebuild vanaf scratch
docker-compose build --no-cache
docker-compose up -d
```

## Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check welke processen poorten gebruiken
   netstat -tulpn | grep :8000
   netstat -tulpn | grep :5432
   ```

2. **Database connection errors**
   ```bash
   # Check database status
   docker-compose exec postgres pg_isready -U testuser -d testdb
   ```

3. **Migration errors**
   ```bash
   # Reset migrations (VOORZICHTIG!)
   docker-compose exec web python manage.py migrate --fake-initial
   ```

4. **Static files issues**
   ```bash
   # Collectstatic opnieuw
   docker-compose exec web python manage.py collectstatic --clear --noinput
   ```

5. **Permission issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

## Test Checklist

- [ ] Docker containers bouwen succesvol
- [ ] Database migraties werken
- [ ] Unit tests passeren
- [ ] Web interface is toegankelijk
- [ ] Batch list toont correct data
- [ ] Batch detail pagina werkt
- [ ] Batch creation werkt
- [ ] Status updates werken
- [ ] Management commands werken
- [ ] API endpoints reageren
- [ ] Notificaties werken
- [ ] Performance is acceptabel
- [ ] Logs tonen geen errors

## Nuttige Commands

```bash
# Container status
docker-compose ps

# Resource usage
docker stats

# Clean rebuild
docker-compose build --no-cache && docker-compose up -d

# Database shell
docker-compose exec postgres psql -U testuser -d testdb

# Django shell
docker-compose exec web python manage.py shell

# Run specific test
docker-compose exec web python manage.py test mill.tests.test_batch_production_service.BatchProductionServiceTest.test_conversion_factor
```

---

*Happy Testing! 🚀*