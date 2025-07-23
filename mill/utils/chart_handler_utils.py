from django.shortcuts import get_object_or_404
from django.utils import timezone
from mill.models import City, Factory, ProductionData, Batch, TransactionData

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.conf import settings
from functools import wraps
from datetime import datetime, date, timedelta
import calendar
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

# Existing time and status checking functions
def check_factory_status(counter_data):
    if counter_data.exists():
        last_entry = counter_data.latest('created_at')
        if timezone.now() - last_entry.created_at < timezone.timedelta(minutes=30):
            return True
    return False

def calculate_start_time(counter_data):
    if counter_data.exists():
        return counter_data.first().created_at.time()
    return 'N/A'

def calculate_stop_time(counter_data, factory_status):
    if factory_status:
        return 'Working'
    if counter_data.exists():
        return counter_data.latest('created_at').created_at.time()
    return 'N/A'

def get_month_ends(target_date, months_back=12):
    # Ensure target_date is a date object
    if isinstance(target_date, datetime):
        target_date = target_date.date()

    month_ends = [target_date]
    current_year = target_date.year
    current_month = target_date.month

    for _ in range(months_back):
        last_day = calendar.monthrange(current_year, current_month)[1]
        end_of_month_date = date(current_year, current_month, last_day)
        if end_of_month_date <= target_date:
            month_ends.append(end_of_month_date)
        # Move to previous month
        current_month -= 1
        if current_month == 0:
            current_month = 12
            current_year -= 1

    return month_ends

def calculate_daily_data(factory_id, selected_date):
    DailyLabels = [(selected_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6)][::-1]
    DailyData = {label: 0 for label in DailyLabels}
    WeeklyData = 0

    production_data = ProductionData.objects.filter(
        device__factory_id=factory_id,
        created_at__date__range=[selected_date - timedelta(days=5), selected_date]
    ).order_by('-created_at')

    for data in production_data:
        date_str = data.created_at.strftime('%Y-%m-%d')
        if date_str in DailyData:
            DailyData[date_str] += data.daily_production  # Sum instead of overwrite
        if date_str == DailyLabels[-1]:
            WeeklyData += data.weekly_production  # Sum weekly data too

    return DailyLabels, [DailyData[label] for label in DailyLabels], WeeklyData

def calculate_hourly_data(factory_id, selected_date):
    # Get all TransactionData for the selected date
    start_datetime = datetime.combine(selected_date, datetime.min.time())
    end_datetime = datetime.combine(selected_date, datetime.max.time())

    production_data = TransactionData.objects.filter(
        device__factory_id=factory_id,
        created_at__range=[start_datetime, end_datetime]
    ).order_by('created_at')

    # Prepare labels for 24 hours
    HourlyLabels = [(start_datetime + timedelta(hours=i)).strftime('%Y-%m-%d %H:00') for i in range(24)]
    HourlyData = {label: 0 for label in HourlyLabels}
    HourlyCounts = {label: 0 for label in HourlyLabels}

    for data in production_data:
        hour_label = data.created_at.strftime('%Y-%m-%d %H:00')
        if hour_label in HourlyData:
            HourlyData[hour_label] += data.daily_production
            HourlyCounts[hour_label] += 1

    # Optionally, average if multiple entries per hour
    HourlyAverages = [
        HourlyData[label] / HourlyCounts[label] if HourlyCounts[label] > 0 else 0
        for label in HourlyLabels
    ]

    return HourlyLabels, HourlyAverages

def calculate_daily_data_batch(factory_id, batch_start_date, selected_date):
    print("calculate_daily_data_batch", batch_start_date, selected_date)
    delta = (selected_date - batch_start_date).days + 1
    DailyLabels = [(batch_start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta)]
    DailyData = {label: 0 for label in DailyLabels}

    # Fixed: Update the date range to use batch_start_date instead of 5 days
    production_data = ProductionData.objects.filter(
        device__factory_id=factory_id,
        created_at__date__range=[batch_start_date, selected_date]
    ).order_by('-created_at')

    print("Production Data Count:", production_data.count())
    print("DailyData:", DailyData)
    
    # Process all data points
    for data in production_data:
        date_str = data.created_at.strftime('%Y-%m-%d')
        if date_str in DailyData:
            DailyData[date_str] += data.daily_production  # Sum instead of overwrite

    return DailyLabels, [DailyData[label] for label in DailyLabels]

def calculate_hourly_data_batch(factory_id, batch_start_date, selected_date):
    # Convert dates to datetime with start and end of day
    start_datetime = batch_start_date
    end_datetime = selected_date
    
    # Get all production data within the date range
    production_data = TransactionData.objects.filter(
        device__factory_id=factory_id,
        created_at__range=[start_datetime, end_datetime]
    ).order_by('created_at')
    
    # Initialize hourly data dictionary
    hourly_data = {}
    
    # Process each production data entry
    for data in production_data:
        # Format datetime to 'YYYY-MM-DD HH:00' to group by hour
        hour_key = data.created_at.strftime('%Y-%m-%d %H:00')
        
        if hour_key not in hourly_data:
            hourly_data[hour_key] = {
                'count': 0,
                'total_production': 0,
            }
        
        hourly_data[hour_key]['count'] += 1
        hourly_data[hour_key]['total_production'] += data.daily_production
    
    # Create sorted lists for labels and data
    hourly_labels = sorted(hourly_data.keys())
    hourly_values = [
        hourly_data[label]['total_production'] / hourly_data[label]['count'] 
        if hourly_data[label]['count'] > 0 else 0 
        for label in hourly_labels
    ]
    
    return hourly_labels, hourly_values

def get_month_ends(target_date, months_back=12):
    if isinstance(target_date, datetime):
        target_date = target_date.date()

    month_ends = [target_date]
    current_year = target_date.year
    current_month = target_date.month

    for _ in range(months_back):
        last_day = calendar.monthrange(current_year, current_month)[1]
        end_of_month_date = date(current_year, current_month, last_day)
        if end_of_month_date <= target_date:
            month_ends.append(end_of_month_date)
        current_month -= 1
        if current_month == 0:
            current_month = 12
            current_year -= 1

    return month_ends

def calculate_monthly_data(factory_id, selected_date):
    MonthlyLabels = [(selected_date - timedelta(days=30 * i)).strftime('%Y-%m') for i in range(12)][::-1]
    MonthlyData = {label: 0 for label in MonthlyLabels}
    month_ends = get_month_ends(selected_date)
    
    production_data = ProductionData.objects.filter(
        device__factory_id=factory_id,
        created_at__date__in=month_ends
    ).order_by('created_at')

    for data in production_data:
        month_str = data.created_at.strftime('%Y-%m')
        if month_str in MonthlyData:
            MonthlyData[month_str] += data.monthly_production  # Sum instead of overwrite

    return MonthlyLabels, [MonthlyData[label] for label in MonthlyLabels]

def calculate_yearly_data(factory_id, selected_date):
    current_year = selected_date.year
    previous_year = current_year - 1

    # Sum all current year data from all devices in the factory
    current_year_data = ProductionData.objects.filter(
        device__factory_id=factory_id,
        created_at__year=current_year
    )
    YearlyCurrent = sum(data.yearly_production for data in current_year_data) if current_year_data.exists() else 0

    # Sum all previous year data from all devices in the factory
    previous_year_data = ProductionData.objects.filter(
        device__factory_id=factory_id,
        created_at__year=previous_year
    )
    YearlyPrevious = sum(data.yearly_production for data in previous_year_data) if previous_year_data.exists() else 0

    return YearlyCurrent, YearlyPrevious

def calculate_batch_actual_production(batch):
    batch_recent_value = ProductionData.objects.filter(
        device__factory=batch.factory,
    ).order_by('-created_at').first()
    if batch_recent_value is None:
        # There is no ProductionData for this factory
        return 0

    # Remove or keep the print as you need for debugging
    # print(batch_recent_value.device)
    # print(batch_recent_value.created_at, batch_recent_value.yearly_production, batch.start_value)

    return batch_recent_value.yearly_production - batch.start_value

def calculate_batch_expected_production(batch, selected_date):

    delta = (selected_date - batch.start_date).days + 1
    return (batch.expected_flour_output/30 * delta)   # Example calculation


def calculate_batch_chart_data(batch_id):

    batch = get_object_or_404(Batch, id=batch_id)
    if batch.end_date:
        date = batch.end_date
    else:
         date = timezone.now()
    
    DailyLabels, DailyData = calculate_daily_data_batch(batch.factory, batch.start_date, date)
    HourlyLabels, HourlyData = calculate_hourly_data_batch(batch.factory, batch.start_date, date)
    batch_actual_production = calculate_batch_actual_production(batch)
    batch_expected_production = calculate_batch_expected_production(batch, date)*1000

    return {
        "hourly_label":HourlyLabels,
        "hourly_data": HourlyData,

        "daily_labels": DailyLabels,
        "daily_data": DailyData,

        "peresent_data":{
        "Actual": batch_actual_production,
        "Expected": batch_expected_production,  
        "waste_ratio" : batch.waste_factor or 0.2,
        },
        "batch_id": batch_id,
        "batch_number": batch.batch_number,
        "batch_start_date": batch.start_date,
        "batch_status": batch.get_status_display(),
        "date": date,
}

def calculate_chart_data(date, factory_id):
    selected_date = datetime.strptime(date, '%Y-%m-%d') if isinstance(date, str) else date
    hourly_labels, hourly_data = calculate_hourly_data(factory_id, selected_date)

    DailyLabels, DailyData, WeeklyData = calculate_daily_data(factory_id, selected_date)
    MonthlyLabels, MonthlyData = calculate_monthly_data(factory_id, selected_date)
    YearlyCurrent, YearlyPrevious = calculate_yearly_data(factory_id, selected_date)

    return {
        "hourly_labels": hourly_labels,
        "hourly_data": hourly_data,
        'daily_labels': DailyLabels,
        'daily_data': DailyData,
        'monthly_labels': MonthlyLabels,
        'monthly_data': MonthlyData,
        'yearly_current': YearlyCurrent,
        'yearly_previous': YearlyPrevious,
        'daily_total': DailyData[-1],
        'monthly_total': MonthlyData[-1],
        'weekly_total': WeeklyData
    }

def calculate_date_range_data(factory_id, start_date, end_date):
    """
    Calculate production data for a specific date range
    """
    start_date = datetime.strptime(start_date, '%Y-%m-%d') if isinstance(start_date, str) else start_date
    end_date = datetime.strptime(end_date, '%Y-%m-%d') if isinstance(end_date, str) else end_date
    
    # Get production data for the date range
    production_data = ProductionData.objects.filter(
        device__factory_id=factory_id,
        created_at__date__range=[start_date.date(), end_date.date()]
    ).order_by('created_at')
    
    # Create daily data dictionary
    daily_data = {}
    current_date = start_date.date()
    while current_date <= end_date.date():
        daily_data[current_date.strftime('%Y-%m-%d')] = 0
        current_date += timedelta(days=1)
    
    # Fill in actual production data
    for data in production_data:
        date_str = data.created_at.strftime('%Y-%m-%d')
        if date_str in daily_data:
            daily_data[date_str] = data.daily_production
    
    # Calculate totals
    total_production = sum(daily_data.values())
    daily_labels = list(daily_data.keys())
    daily_values = list(daily_data.values())
    
    return {
        'daily_labels': daily_labels,
        'daily_data': daily_values,
        'total_production': total_production,
        'date_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        'days_count': len(daily_labels)
    }

def calculate_device_chart_data(date, factory_id, device_id):
    """Calculate chart data for a specific device"""
    selected_date = datetime.strptime(date, '%Y-%m-%d') if isinstance(date, str) else date
    
    # Filter by specific device
    device_filter = {'device_id': device_id, 'device__factory_id': factory_id}
    
    # Calculate hourly data for specific device
    start_datetime = datetime.combine(selected_date, datetime.min.time())
    end_datetime = datetime.combine(selected_date, datetime.max.time())

    production_data = TransactionData.objects.filter(
        device_id=device_id,
        device__factory_id=factory_id,
        created_at__range=[start_datetime, end_datetime]
    ).order_by('created_at')

    # Prepare labels for 24 hours
    HourlyLabels = [(start_datetime + timedelta(hours=i)).strftime('%Y-%m-%d %H:00') for i in range(24)]
    HourlyData = {label: 0 for label in HourlyLabels}
    HourlyCounts = {label: 0 for label in HourlyLabels}

    for data in production_data:
        hour_label = data.created_at.strftime('%Y-%m-%d %H:00')
        if hour_label in HourlyData:
            HourlyData[hour_label] += data.daily_production
            HourlyCounts[hour_label] += 1

    # Optionally, average if multiple entries per hour
    HourlyAverages = [
        HourlyData[label] / HourlyCounts[label] if HourlyCounts[label] > 0 else 0
        for label in HourlyLabels
    ]

    # Calculate daily data for specific device
    DailyLabels = [(selected_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6)][::-1]
    DailyData = {label: 0 for label in DailyLabels}
    WeeklyData = 0

    production_data = ProductionData.objects.filter(
        device_id=device_id,
        device__factory_id=factory_id,
        created_at__date__range=[selected_date - timedelta(days=5), selected_date]
    ).order_by('-created_at')

    for data in production_data:
        date_str = data.created_at.strftime('%Y-%m-%d')
        if date_str in DailyData:
            DailyData[date_str] = data.daily_production
        if date_str == DailyLabels[-1]:
            WeeklyData = data.weekly_production

    # Calculate monthly data for specific device
    MonthlyLabels = [(selected_date - timedelta(days=30 * i)).strftime('%Y-%m') for i in range(12)][::-1]
    MonthlyData = {label: 0 for label in MonthlyLabels}
    month_ends = get_month_ends(selected_date)
    
    production_data = ProductionData.objects.filter(
        device_id=device_id,
        device__factory_id=factory_id,
        created_at__date__in=month_ends
    ).order_by('created_at')

    for data in production_data:
        month_str = data.created_at.strftime('%Y-%m')
        if month_str in MonthlyData:
            MonthlyData[month_str] = data.monthly_production

    # Calculate yearly data for specific device
    current_year = selected_date.year
    previous_year = current_year - 1

    last_current_year_entry = ProductionData.objects.filter(
        device_id=device_id,
        device__factory_id=factory_id,
        created_at__year=current_year
    ).order_by('-created_at').first()
    YearlyCurrent = last_current_year_entry.yearly_production if last_current_year_entry else 0

    last_previous_year_entry = ProductionData.objects.filter(
        device_id=device_id,
        device__factory_id=factory_id,
        created_at__year=previous_year
    ).order_by('-created_at').first()
    YearlyPrevious = last_previous_year_entry.yearly_production if last_previous_year_entry else 0

    return {
        "hourly_labels": HourlyLabels,
        "hourly_data": HourlyAverages,
        'daily_labels': DailyLabels,
        'daily_data': [DailyData[label] for label in DailyLabels],
        'monthly_labels': MonthlyLabels,
        'monthly_data': [MonthlyData[label] for label in MonthlyLabels],
        'yearly_current': YearlyCurrent,
        'yearly_previous': YearlyPrevious,
        'daily_total': DailyData[DailyLabels[-1]] if DailyLabels else 0,
        'monthly_total': MonthlyData[MonthlyLabels[-1]] if MonthlyLabels else 0,
        'weekly_total': WeeklyData
    }

# Email notification function
def send_notification_email(user, notification):
    subject = f"New Notification: {notification.category.name}"
    message = f"""
    {notification.message}
    View details: {notification.link or ''}
    """
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )
