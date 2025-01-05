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
