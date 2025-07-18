from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
import csv
import xlsxwriter
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from mill.models import City, Factory, Device, ProductionData

@login_required
def preview_data(request):
    # Previous preview_data function remains unchanged
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        factory_ids = request.GET.getlist('factory_ids')

        # Convert dates
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)

        # Query the data with limit for multiple factories
        production_data = ProductionData.objects.filter(
            device__factory_id__in=factory_ids,
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
    if request.user.groups.filter(name='Superadmin').exists():
        cities = City.objects.all()
    else:
        cities = request.user.userprofile.allowed_cities.all()

    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        selected_cities = request.POST.getlist('cities')
        selected_factories = request.POST.getlist('factories')
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

            # Validate city and factory selection
            if not selected_cities:
                raise ValueError("Please select at least one city")
            
            if not selected_factories:
                raise ValueError("Please select at least one factory")

            # Validate that factories belong to the selected cities
            try:
                factories = Factory.objects.filter(
                    id__in=selected_factories,
                    city_id__in=selected_cities
                )
                if factories.count() != len(selected_factories):
                    raise ValueError("Some selected factories do not belong to the selected cities")
            except Factory.DoesNotExist:
                raise ValueError("Selected factories do not belong to the selected cities")

            # Query the data for the selected factories
            devices = Device.objects.filter(factory__in=factories)
            production_data = ProductionData.objects.filter(
                device__in=devices,
                created_at__range=(start_date, end_date)
            ).select_related(
                'device', 
                'device__factory', 
                'device__factory__city'
            ).order_by('device__factory__city__name', 'device__factory__name', 'created_at')
            
            # Check if there's data to export
            if not production_data.exists():
                messages.warning(request, f"No production data found for the selected date range ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}) and factories. Please try a different date range or check if factories have production data.")
                return redirect('export_data')

            # Define headers
            headers = [
                'Date', 'City', 'City Status', 'Factory Name', 'Factory Status',
                'Factory Error', 'Device ID', 'Device Name', 'Device Status',
                'Selected Counter', 'Daily Production', 'Weekly Production',
                'Monthly Production', 'Yearly Production', 'Last Updated'
            ]

            # Generate filename based on selection
            if len(factories) == 1:
                filename_base = f"factory_data_{factories.first().name}"
            elif len(selected_cities) == 1:
                filename_base = f"city_data_{factories.first().city.name}"
            else:
                filename_base = f"multi_factory_data"

            if export_format == 'csv':
                # Create CSV with proper UTF-8 encoding
                response = HttpResponse(content_type='text/csv; charset=utf-8')
                response['Content-Disposition'] = f'attachment; filename="{filename_base}_{start_date.strftime("%Y%m%d")}_to_{end_date.strftime("%Y%m%d")}.csv"'
                response.write('\ufeff')  # BOM for Excel UTF-8 compatibility
                
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

            elif export_format == 'excel':
                # Create Excel file with simple formatting
                response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="{filename_base}_{start_date.strftime("%Y%m%d")}_to_{end_date.strftime("%Y%m%d")}.xlsx"'
                
                try:
                    # Create workbook and worksheet
                    workbook = xlsxwriter.Workbook(response)
                    worksheet = workbook.add_worksheet('Factory Data')
                    
                    # Simple header format
                    header_format = workbook.add_format({
                        'bold': True,
                        'bg_color': '#D7E4BC',
                        'border': 1
                    })
                    
                    # Simple data format
                    data_format = workbook.add_format({
                        'border': 1
                    })
                    
                    # Write headers
                    for col, header in enumerate(headers):
                        worksheet.write(0, col, header, header_format)
                    
                    # Set column widths
                    column_widths = [20, 15, 12, 25, 12, 12, 10, 20, 12, 15, 15, 15, 15, 15, 20]
                    for col, width in enumerate(column_widths):
                        worksheet.set_column(col, col, width)
                    
                    # Write data (limit to first 1000 records to avoid timeout)
                    data_to_write = list(production_data[:1000])
                    for row, data in enumerate(data_to_write, start=1):
                        worksheet.write(row, 0, data.created_at.strftime('%Y-%m-%d %H:%M:%S'), data_format)
                        worksheet.write(row, 1, data.device.factory.city.name, data_format)
                        worksheet.write(row, 2, 'Active' if data.device.factory.city.status else 'Inactive', data_format)
                        worksheet.write(row, 3, data.device.factory.name, data_format)
                        worksheet.write(row, 4, 'Active' if data.device.factory.status else 'Inactive', data_format)
                        worksheet.write(row, 5, 'Yes' if data.device.factory.error else 'No', data_format)
                        worksheet.write(row, 6, data.device.id, data_format)
                        worksheet.write(row, 7, data.device.name, data_format)
                        worksheet.write(row, 8, 'Active' if data.device.status else 'Inactive', data_format)
                        worksheet.write(row, 9, data.device.selected_counter, data_format)
                        worksheet.write(row, 10, data.daily_production, data_format)
                        worksheet.write(row, 11, data.weekly_production, data_format)
                        worksheet.write(row, 12, data.monthly_production, data_format)
                        worksheet.write(row, 13, data.yearly_production, data_format)
                        worksheet.write(row, 14, data.updated_at.strftime('%Y-%m-%d %H:%M:%S'), data_format)
                    
                    # Add summary
                    summary_row = len(data_to_write) + 2
                    worksheet.write(summary_row, 0, 'SUMMARY', header_format)
                    worksheet.write(summary_row + 1, 0, f'Total Records: {len(data_to_write)} (showing first 1000)', data_format)
                    worksheet.write(summary_row + 2, 0, f'Total Daily Production: {sum(d.daily_production for d in data_to_write)}', data_format)
                    
                    workbook.close()
                    
                except Exception as e:
                    messages.error(request, f"Error creating Excel file: {str(e)}")
                    return redirect('export_data')

            else:  # PDF export
                # Create the response object for PDF
                buffer = BytesIO()
                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=A4,  # Use portrait instead of landscape
                    rightMargin=20,
                    leftMargin=20,
                    topMargin=30,
                    bottomMargin=30
                )

                # Create the PDF content
                elements = []
                
                # Register Arabic font (using built-in Helvetica for now)
                # For better Arabic support, you would need to add a TTF font file
                styles = getSampleStyleSheet()
                if len(factories) == 1:
                    factory_name = factories.first().name
                    # Check if factory name is Arabic and use ID instead
                    if any(ord(char) > 127 for char in factory_name):
                        factory_name = f"Factory-{factories.first().id}"
                    title_text = f"Factory Data Report - {factory_name}"
                elif len(selected_cities) == 1:
                    city_name = factories.first().city.name
                    # Check if city name is Arabic and use English equivalent
                    if any(ord(char) > 127 for char in city_name):
                        city_mapping = {
                            'كربلاء': 'Karbalaa',
                            'المثنى': 'Alsamawah', 
                            'الديوانية': 'Al-Diwaniya',
                            'بابل': 'Hilla',
                            'بغداد': 'Baghdad',
                            'الانبار': 'Anbar',
                            'دهوك': 'Duhok'
                        }
                        city_name = city_mapping.get(city_name, f"City-{factories.first().city.id}")
                    title_text = f"City Data Report - {city_name}"
                else:
                    title_text = f"Multi-Factory Data Report"
                
                title = Paragraph(title_text, styles['Heading1'])
                elements.append(title)
                
                # Add subtitle with date range
                subtitle = Paragraph(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", styles['Normal'])
                elements.append(subtitle)
                
                # Add summary statistics
                elements.append(Paragraph("<br/>", styles['Normal']))
                summary_data = [
                    ['Summary Statistics', ''],
                    ['Total Records', str(len(production_data))],
                    ['Total Daily Production', f"{sum(d.daily_production for d in production_data):,}"],
                    ['Total Monthly Production', f"{sum(d.monthly_production for d in production_data):,}"],
                ]
                
                summary_table = Table(summary_data, colWidths=[150, 100])
                summary_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONT', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                elements.append(summary_table)
                
                # Add space before main table
                elements.append(Paragraph("<br/><br/>", styles['Normal']))

                # Simplified headers for better fit
                simplified_headers = [
                    'Date', 'City', 'Factory', 'Device', 'Status', 
                    'Daily', 'Monthly'
                ]
                
                # Prepare data for table (limit to first 500 records for PDF)
                table_data = [simplified_headers]  # Add headers first
                data_to_show = list(production_data[:500])
                
                for data in data_to_show:
                    # Smart name handling - use English names when available, IDs for Arabic
                    city_name = data.device.factory.city.name
                    factory_name = data.device.factory.name
                    device_name = data.device.name
                    
                    # Check if names contain Arabic characters and replace with readable alternatives
                    def is_arabic(text):
                        return any(ord(char) > 127 for char in text)
                    
                    # For cities, try to use English equivalents
                    if is_arabic(city_name):
                        city_mapping = {
                            'كربلاء': 'Karbalaa',
                            'المثنى': 'Alsamawah', 
                            'الديوانية': 'Al-Diwaniya',
                            'بابل': 'Hilla',
                            'بغداد': 'Baghdad',
                            'الانبار': 'Anbar',
                            'دهوك': 'Duhok'
                        }
                        city_name = city_mapping.get(city_name, f"City-{data.device.factory.city.id}")
                    
                    # For factories and devices, use ID-based names for Arabic
                    if is_arabic(factory_name):
                        factory_name = f"Factory-{data.device.factory.id}"
                    if is_arabic(device_name):
                        device_name = f"Device-{data.device.id}"
                    
                    row = [
                        data.created_at.strftime('%Y-%m-%d'),
                        city_name,
                        factory_name,
                        device_name,
                        'Active' if data.device.status else 'Inactive',
                        f"{data.daily_production:,}",
                        f"{data.monthly_production:,}"
                    ]
                    table_data.append(row)

                # Create the table with better column widths
                table = Table(table_data, colWidths=[60, 60, 80, 60, 40, 50, 50])
                table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (1, 1), (3, -1), 'LEFT'),  # Text columns left-aligned
                    ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONT', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),  # Smaller font for better fit
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('WORDWRAP', (1, 1), (3, -1), True),  # Enable word wrapping for text columns
                ]))

                elements.append(table)
                
                # Add note about data limit
                if len(production_data) > 500:
                    elements.append(Paragraph("<br/>", styles['Normal']))
                    note = Paragraph(f"Note: Showing first 500 records out of {len(production_data)} total records", styles['Normal'])
                    elements.append(note)
                
                # Add note about Arabic text
                elements.append(Paragraph("<br/>", styles['Normal']))
                arabic_note = Paragraph("Note: Arabic names are converted to English equivalents or IDs for better PDF readability. Use Excel export for full Arabic text support.", styles['Normal'])
                elements.append(arabic_note)
                
                # Build PDF document
                doc.build(elements)
                
                # Get the value of the BytesIO buffer and create the response
                pdf = buffer.getvalue()
                buffer.close()
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{filename_base}_{start_date.strftime("%Y%m%d")}_to_{end_date.strftime("%Y%m%d")}.pdf"'
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