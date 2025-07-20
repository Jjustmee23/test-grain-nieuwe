from django.core.management.base import BaseCommand
from mill.models import Factory

class Command(BaseCommand):
    help = 'Add sample addresses for key factories'

    def handle(self, *args, **options):
        # Sample addresses for key factories in Iraq
        sample_addresses = {
            # Baghdad factories
            283: {  # مطحنة بغداد
                'address': 'Al-Rashid Street, Baghdad, Iraq',
                'latitude': 33.3152,
                'longitude': 44.3661
            },
            33: {   # مطحنة المتحدة 1
                'address': 'Al-Karrada, Baghdad, Iraq',
                'latitude': 33.3152,
                'longitude': 44.3661
            },
            64: {   # مطحنة المتحدة 2
                'address': 'Al-Mansour, Baghdad, Iraq',
                'latitude': 33.3152,
                'longitude': 44.3661
            },
            228: {  # مطحنة المنصور
                'address': 'Al-Mansour District, Baghdad, Iraq',
                'latitude': 33.3152,
                'longitude': 44.3661
            },
            
            # Karbala factories
            346: {  # مطحنة الحسين الحكومية
                'address': 'Karbala City Center, Karbala, Iraq',
                'latitude': 32.6027,
                'longitude': 44.0195
            },
            20: {   # مطحنة نور السبطين 1
                'address': 'Al-Hussein District, Karbala, Iraq',
                'latitude': 32.6027,
                'longitude': 44.0195
            },
            21: {   # مطحنة نور السبطين 2
                'address': 'Al-Abbas District, Karbala, Iraq',
                'latitude': 32.6027,
                'longitude': 44.0195
            },
            
            # Kirkuk factories
            348: {  # مطحنة كركوك الحكومية
                'address': 'Kirkuk City Center, Kirkuk, Iraq',
                'latitude': 35.4681,
                'longitude': 44.3922
            },
            300: {  # مطحنة كركوك
                'address': 'Al-Quds District, Kirkuk, Iraq',
                'latitude': 35.4681,
                'longitude': 44.3922
            },
            
            # Duhok factories
            63: {   # مطحنة دستار 1
                'address': 'Duhok City Center, Duhok, Iraq',
                'latitude': 36.8671,
                'longitude': 42.9884
            },
            62: {   # مطحنة دستار 2
                'address': 'Duhok Industrial Area, Duhok, Iraq',
                'latitude': 36.8671,
                'longitude': 42.9884
            },
            
            # Diyala factories
            370: {  # مطحنة ديالى الحكومية
                'address': 'Baqubah City Center, Diyala, Iraq',
                'latitude': 33.7486,
                'longitude': 44.6439
            },
            117: {  # مطحنة بعقوبة
                'address': 'Baqubah Industrial Zone, Diyala, Iraq',
                'latitude': 33.7486,
                'longitude': 44.6439
            },
            
            # Dhi Qar factories
            358: {  # مطحنة سومر الحكومية
                'address': 'Nasiriyah City Center, Dhi Qar, Iraq',
                'latitude': 31.0581,
                'longitude': 46.2574
            },
            201: {  # مطحنة ذي قار الفني
                'address': 'Nasiriyah Industrial Area, Dhi Qar, Iraq',
                'latitude': 31.0581,
                'longitude': 46.2574
            },
            
            # Salah Aldin factories
            378: {  # مطحنة السنبلة صلاح الدين
                'address': 'Tikrit City Center, Salah Aldin, Iraq',
                'latitude': 34.5983,
                'longitude': 43.6769
            },
            
            # Maysan factories
            360: {  # مطحنة العمارة الحكومية
                'address': 'Amarah City Center, Maysan, Iraq',
                'latitude': 31.8347,
                'longitude': 47.1447
            },
            
            # Wasit factories
            359: {  # مطحنة المتنبي الحكومية
                'address': 'Kut City Center, Wasit, Iraq',
                'latitude': 32.5128,
                'longitude': 45.8182
            }
        }

        updated_count = 0
        error_count = 0

        for factory_id, address_data in sample_addresses.items():
            try:
                factory = Factory.objects.get(id=factory_id)
                
                factory.address = address_data['address']
                factory.latitude = address_data['latitude']
                factory.longitude = address_data['longitude']
                factory.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Updated {factory.name} ({factory.city.name}): {address_data["address"]}')
                )
                updated_count += 1
                
            except Factory.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Factory with ID {factory_id} not found')
                )
                error_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error updating factory {factory_id}: {str(e)}')
                )
                error_count += 1

        self.stdout.write('\n' + '='*50)
        self.stdout.write('SUMMARY:')
        self.stdout.write(f'Successfully updated: {updated_count}')
        self.stdout.write(f'Errors: {error_count}')
        self.stdout.write(f'Total processed: {len(sample_addresses)}') 