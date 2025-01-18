from django.shortcuts import get_object_or_404
from django.utils import timezone

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


from datetime import datetime, timedelta
from mill.models import City, Factory, ProductionData

def calculate_daily_data(factory_id,selected_date):
    print(selected_date, factory_id)
    # Initial Daily Labels: Last 6 days including the selected date
    DailyLabels = [(selected_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6)][::-1]
    DailyData = {label: 0 for label in DailyLabels}
    WeeklyData = 0
    print(DailyLabels,"jhghjgjh",DailyData)
    # Get production entries for the last 6 days
    production_data = ProductionData.objects.filter(
        device__factory_id=factory_id,
        created_at__date__range=[selected_date - timedelta(days=5), selected_date]
    ).order_by('-created_at')

    # Map existing data to the corresponding labels
    for data in production_data:
        date_str = data.created_at.strftime('%Y-%m-%d')
        if date_str in DailyData:
            DailyData[date_str] = data.daily_production
        if date_str == DailyLabels[-1]:
            print("Date not in labels")
            WeeklyData = data.weekly_production
        print(DailyLabels[-1],date_str)

    return DailyLabels, [DailyData[label] for label in DailyLabels], WeeklyData

from datetime import date, timedelta
import calendar

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


def calculate_monthly_data(factory_id,selected_date):
    MonthlyLabels = [(selected_date - timedelta(days=30 * i)).strftime('%Y-%m') for i in range(12)][::-1]
    # Initialize data with zeros
    MonthlyData = {label: 0 for label in MonthlyLabels}
    month_ends = get_month_ends(selected_date)
    production_data = ProductionData.objects.filter(
        device__factory_id=factory_id,
        created_at__date__in=month_ends
    ).order_by('created_at')

    # Map existing data to the corresponding labels
    for data in production_data:
        month_str = data.created_at.strftime('%Y-%m')
        if month_str in MonthlyData:
            MonthlyData[month_str] = data.monthly_production

    # Return labels and data as a list
    return MonthlyLabels, [MonthlyData[label] for label in MonthlyLabels]

def calculate_yearly_data(factory_id,selected_date):
    current_year = selected_date.year
    previous_year = current_year - 1
        # Current Year: Last created yearly_production value
    last_current_year_entry = ProductionData.objects.filter(
        device__factory_id=factory_id,
        created_at__year=current_year
    ).order_by('-created_at').first()
    YearlyCurrent = last_current_year_entry.yearly_production if last_current_year_entry else 0

    # Previous Year: Last created yearly_production value
    last_previous_year_entry = ProductionData.objects.filter(
        device__factory_id=factory_id,
        created_at__year=previous_year
    ).order_by('-created_at').first()
    YearlyPrevious = last_previous_year_entry.yearly_production if last_previous_year_entry else 0
    return YearlyCurrent, YearlyPrevious


def calculate_chart_data(date,factory_id):
        # Convert date to datetime object if not already
    selected_date = datetime.strptime(date, '%Y-%m-%d') if isinstance(date, str) else date
    
    DailyLabels, DailyData, WeeklyData = calculate_daily_data(factory_id, selected_date)
    print("Daily:_______",DailyLabels, DailyData)
    MonthlyLabels, MonthlyData = calculate_monthly_data(factory_id, selected_date)
    print("Monthly:_______",MonthlyLabels, MonthlyData)
    YearlyCurrent, YearlyPrevious = calculate_yearly_data(factory_id, selected_date)
    print("Yearly:_______",YearlyCurrent, YearlyPrevious)

    return { 'daily_labels': DailyLabels, 'daily_data': DailyData, 'monthly_labels': MonthlyLabels, 'monthly_data': MonthlyData, 'yearly_current': YearlyCurrent, 'yearly_previous': YearlyPrevious , 'daily_total': DailyData[-1], 'monthly_total': MonthlyData[-1], 'weekly_total': WeeklyData}


# Check Allowlists
def is_allowed_factory(request, factory_id):
    factory = get_object_or_404(Factory, id=factory_id)
    if request.user.groups.filter(name='Superadmin').exists():
        return factory
    if request.user.userprofile.allowed_cities.filter(id=factory.city.id).exists():
        return factory
    return None
    
def is_allowed_city(request, city_id):
    city = get_object_or_404(City, id=city_id)
    if request.user.groups.filter(name='Superadmin').exists():
        return city
    if request.user.userprofile.allowed_cities.filter(id=city.id).exists():
        return city
    return None

def allowed_cities(request):
    if request.user.groups.filter(name='Superadmin').exists():
        print("SU allowed all cities")
        return City.objects.all()
    print(request.user.userprofile.allowed_cities.all())
    return request.user.userprofile.allowed_cities.all()
def allowed_factories(request):
    if request.user.groups.filter(name='Superadmin').exists():
        print("Superadmin detected. Returning all factories.")
        return Factory.objects.all()
    print("Returning allowed factories.")
    print(request.user.userprofile.allowed_cities.all())
    return Factory.objects.filter(city__in=request.user.userprofile.allowed_cities.all())