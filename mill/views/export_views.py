from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
import csv
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from mill.models import City, Factory, Device, ProductionData

@login_required
def preview_data(request):
    # Previous preview_data function remains unchanged
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        cities = request.GET.get('cities', '').split(',')

        # Convert dates
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)

        # Query the data with limit
        production_data = ProductionData.objects.filter(
            device__factory__city_id__in=cities,
            created_at__range=(start_date, end_date)
        ).select_related(
            'device', 
            'device__factory', 
            'device__factory__city'
        ).order_by('-created_at')[:100]

        preview_data = [{
            'created_at': data.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'city_name': data.device.factory.city.name,
            'factory_name': data.device.factory.name,
            'device_name': data.device.name,
            'status': data.device.status,
            'daily_production': data.daily_production,
            'weekly_production': data.weekly_production,
            'monthly_production': data.monthly_production,
            'yearly_production': data.yearly_production
        } for data in production_data]

        return JsonResponse(preview_data, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

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
        export_format = request.POST.get('export_format', 'csv')  # Default to CSV if not specified

        try:
            # Convert string dates to datetime objects
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Add time to make end_date inclusive
            end_date = end_date.replace(hour=23, minute=59, second=59)

            # Validate date range
            if start_date > end_date:
                raise ValueError("Start date cannot be later than end date")

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

            # Define headers
            headers = [
                'Date', 'City', 'City Status', 'Factory Name', 'Factory Status',
                'Factory Error', 'Device ID', 'Device Name', 'Device Status',
                'Selected Counter', 'Daily Production', 'Weekly Production',
                'Monthly Production', 'Yearly Production', 'Last Updated'
            ]

            if export_format == 'csv':
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="factory_data_{start_date.strftime("%Y%m%d")}_to_{end_date.strftime("%Y%m%d")}.csv"'
                writer = csv.writer(response)
                writer.writerow(headers)

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

            else:  # PDF export
                # Create the response object for PDF
                buffer = BytesIO()
                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=landscape(A4),
                    rightMargin=30,
                    leftMargin=30,
                    topMargin=30,
                    bottomMargin=30
                )

                # Create the PDF content
                elements = []
                
                # Add title
                styles = getSampleStyleSheet()
                title = Paragraph(
                    f"Factory Data Report ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})",
                    styles['Heading1']
                )
                elements.append(title)

                # Prepare data for table
                table_data = [headers]  # Add headers first
                for data in production_data:
                    row = [
                        data.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        data.device.factory.city.name,
                        'Active' if data.device.factory.city.status else 'Inactive',
                        data.device.factory.name,
                        'Active' if data.device.factory.status else 'Inactive',
                        'Yes' if data.device.factory.error else 'No',
                        str(data.device.id),
                        data.device.name,
                        'Active' if data.device.status else 'Inactive',
                        str(data.device.selected_counter),
                        str(data.daily_production),
                        str(data.weekly_production),
                        str(data.monthly_production),
                        str(data.yearly_production),
                        data.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                    ]
                    table_data.append(row)

                # Create the table
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONT', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))

                elements.append(table)
                
                # Build PDF document
                doc.build(elements)
                
                # Get the value of the BytesIO buffer and create the response
                pdf = buffer.getvalue()
                buffer.close()
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="factory_data_{start_date.strftime("%Y%m%d")}_to_{end_date.strftime("%Y%m%d")}.pdf"'
                response.write(pdf)

            return response

        except (ValueError, TypeError) as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('export_data')

    context = {
        'cities': cities,
    }
    if request.method == 'GET':
        # Get today's data for preview
        today = timezone.now()
        preview_data = ProductionData.objects.filter(
            created_at__date=today.date()
        ).select_related(
            'device', 
            'device__factory', 
            'device__factory__city'
        ).order_by('-created_at')[:50]

        context.update({
            'preview_data': preview_data,
        })
    return render(request, 'mill/export_data.html', context)