from django.shortcuts import render, get_object_or_404, redirect
from mill.models import Factory, City

def manage_factory(request):
    cities = City.objects.all()
    factories = Factory.objects.all().select_related('city')
    return render(request, 'mill/manage_factory.html', {'factories': factories, 'cities': cities})
