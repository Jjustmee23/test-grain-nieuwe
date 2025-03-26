from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
import csv
from mill.models import City, Factory, Device, ProductionData

@login_required
def export_data(request):
    # Get cities available to the user
    if request.user.groups.filter(name='super_admin').exists():
        cities = City.objects.all()
    else:
        cities = request.user.userprofile.allowed_cities.all()

    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        selected_cities = request.POST.getlist('cities')

        try:
            # Convert string dates to datetime objects
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Add time to make end_date inclusive
            end_date = end_date.replace(hour=23, minute=59, second=59)

            # Validate date range
            if start_date > end_date:
                raise ValueError("Start date cannot be later than end date")

            # Create the HttpResponse object with CSV header
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="factory_data_{start_date.strftime("%Y%m%d")}_to_{end_date.strftime("%Y%m%d")}.csv"'

            # Create CSV writer
            writer = csv.writer(response)
            writer.writerow([
                'Date',
                'City',
                'City Status',
                'Factory Name',
                'Factory Status',
                'Factory Error',
                'Device ID',
                'Device Name',
                'Device Status',
                'Selected Counter',
                'Daily Production',
                'Weekly Production',
                'Monthly Production',
                'Yearly Production',
                'Last Updated'
            ])

            # Query the data
            factories = Factory.objects.filter(city_id__in=selected_cities)
            devices = Device.objects.filter(factory__in=factories)
            
            production_data = ProductionData.objects.filter(
                device__in=devices,
                created_at__range=(start_date, end_date)
            ).select_related(
                'device', 
                'device__factory', 
                'device__factory__city'
            )

            # Write data rows
            for data in production_data:
                writer.writerow([
                    data.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    data.device.factory.city.name,
                    'Active' if data.device.factory.city.status else 'Inactive',
                    data.device.factory.name,
                    'Active' if data.device.factory.status else 'Inactive',
                    'Yes' if data.device.factory.error else 'No',
                    data.device.id,
                    data.device.name,
                    'Active' if data.device.status else 'Inactive',
                    data.device.selected_counter,
                    data.daily_production,
                    data.weekly_production,
                    data.monthly_production,
                    data.yearly_production,
                    data.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                ])

            return response

        except (ValueError, TypeError) as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('export_data')

    context = {
        'cities': cities,
    }
    return render(request, 'mill/export_data.html', context)