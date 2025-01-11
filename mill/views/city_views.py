from django.shortcuts import render, redirect
from mill.models import City, Factory
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def manage_city(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        city_name = request.POST.get('city_name')
        city_id = request.POST.get('city_id')

        print(f"Action: {action}, City Name: {city_name}, City ID: {city_id}")

        if action == 'add_city':
            if not city_name.strip():
                messages.error(request, 'City name cannot be empty!')
                return redirect('manage_city')

            if City.objects.filter(name__iexact=city_name).exists():
                messages.error(request, 'City already exists!')
            else:
                try:
                    City.objects.create(name=city_name)
                    messages.success(request, 'City added successfully!')
                except Exception as e:
                    print(f"Error adding city: {e}")
                    messages.error(request, 'Error adding city!')

        elif action == 'edit_city':
            if not city_name.strip():
                messages.error(request, 'City name cannot be empty!')
                return redirect('manage_city')

            try:
                city = City.objects.get(id=city_id)
                city.name = city_name
                city.save()
                messages.success(request, 'City updated successfully!')
            except City.DoesNotExist:
                messages.error(request, 'City not found!')
            except Exception as e:
                print(f"Error updating city: {e}")
                messages.error(request, 'Error updating city!')

        elif action == 'remove_city':
            try:
                city = City.objects.get(id=city_id)
                city.delete()
                messages.success(request, 'City removed successfully!')
            except City.DoesNotExist:
                messages.error(request, 'City not found!')
            except Exception as e:
                print(f"Error removing city: {e}")
                messages.error(request, 'Error removing city!')

        return redirect('manage_city')

    # Handle GET request
    if request.user.groups.filter(name='super_admin').exists():
        cities = City.objects.all()
    else:
        cities = request.user.userprofile.allowed_cities.all()
    city_data = [
        {
            'id': city.id,
            'name': city.name,
            'factories_count': Factory.objects.filter(city=city).count()
        }
        for city in cities
    ]

    return render(request, 'mill/manage_city.html', {'cities': city_data})
