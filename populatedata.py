# populatedata.py

import os
import django

# Replace 'myproject.settings' with your project's settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import random
from mill.models import City, Factory, Device

def populate_initial_data():
    print('Starting data population...')

    # Create 30 cities
    for city_num in range(1, 31):
        city_name = f'City_{city_num}'
        city, created = City.objects.get_or_create(name=city_name)
        if created:
            print(f'Created {city}')

        # Create 10 factories for each city
        for factory_num in range(1, 11):
            factory_name = f'Factory_{city_num}_{factory_num}'
            factory, created = Factory.objects.get_or_create(
                name=factory_name,
                city=city,
                defaults={'status': True}
            )
            if created:
                print(f'  Created {factory}')

            # Create 1 or 2 devices for each factory
            num_devices = random.choice([1, 2])
            for device_num in range(1, num_devices + 1):
                device_name = f'Device_{city_num}_{factory_num}_{device_num}'
                serial_number = f'SN-{city_num}-{factory_num}-{device_num}-{random.randint(1000,9999)}'
                device, created = Device.objects.get_or_create(
                    name=device_name,
                    serial_number=serial_number,
                    factory=factory,
                    defaults={'status': True}
                )
                if created:
                    print(f'    Created {device}')

    print('Data population completed successfully.')

if __name__ == '__main__':
    populate_initial_data()
