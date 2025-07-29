import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mill.models import Factory, City

print("=== MILLS IN ONS SYSTEEM ===")
factories = Factory.objects.filter(status=True)
print(f"Totaal actieve factories: {factories.count()}")
print()

print("=== ALLE FACTORIES ===")
for i, factory in enumerate(factories, 1):
    city_name = factory.city.name if factory.city else "Geen stad"
    print(f"{i:2d}. {factory.name} ({city_name})")

print()
print("=== FACTORIES PER STAD ===")
cities = {}
for factory in factories:
    city_name = factory.city.name if factory.city else "Geen stad"
    if city_name not in cities:
        cities[city_name] = []
    cities[city_name].append(factory.name)

for city, mills in cities.items():
    print(f"{city}: {len(mills)} mills - {mills}")

print()
print("=== STEDEN IN SYSTEEM ===")
all_cities = City.objects.all()
for city in all_cities:
    print(f"- {city.name}")

print()
print("=== SAMENVATTING ===")
print(f"✅ Totaal actieve factories: {factories.count()}")
print(f"✅ Totaal steden: {all_cities.count()}")
print(f"✅ Factories per stad: {len(cities)}") 