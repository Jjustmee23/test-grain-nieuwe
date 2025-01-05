from django.shortcuts import render, get_object_or_404, redirect
from mill.models import Factory, ProductionData, Device
from datetime import date
from django.contrib.auth.decorators import login_required

@login_required
def view_statistics(request, factory_id):
    # Retrieve the date from GET parameters, or default to today's date
    selected_date = request.GET.get('date', date.today().isoformat())

    #get selected date from query
    factory = get_object_or_404(Factory, id=factory_id)
    devices = Device.objects.filter(factory=factory)
    device_data = ProductionData.objects.filter(
        device = devices[0]
        #selected_date
    )[:50]
    print('Device_dat in statistics',device_data)
    if device_data:
        today_total = device_data[0]
    else:
        today_total = 0
    # Prepare context for rendering the template
    context = {
        'date': selected_date,
        'current_date': date.today().isoformat(),
        'factory': factory,
        'device_data':device_data,
        'device_id':devices[0].id,
        'today_total':today_total
    }
    
    # Render the HTML template with the context
    return render(request, 'mill/view_statistics.html', context)
