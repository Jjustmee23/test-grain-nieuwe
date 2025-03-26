from django.shortcuts import render, get_object_or_404, redirect
# from django.http import JsonResponse
from mill.models import Factory, City, Device
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from mill.utils import allowed_cities, allowed_factories, is_allowed_city, is_allowed_factory


def manage_factory(request):
    # Get search parameters from either GET or POST
    search_query = request.GET.get('search', '').strip()
    city_filter = request.GET.get('city_filter', '')
    
    if request.method == "POST":
        action = request.POST.get('action')
        factory_id = request.POST.get('factory_id')
        device_id = request.POST.get('device_id')

        try:
            if action == "add_device_to_factory":
                with transaction.atomic():
                    factory = Factory.objects.get(id=factory_id)
                    device = Device.objects.select_for_update().get(id=device_id)
                    
                    print(f"Before linking - Device {device.id} factory: {device.factory}")
                    
                    # Force update the device's factory
                    Device.objects.filter(id=device_id).update(factory=factory)
                    
                    # Refresh from database to verify
                    device.refresh_from_db()
                    print(f"After linking - Device {device.id} factory: {device.factory}")
                    
                    if device.factory == factory:
                        messages.success(request, f"Device '{device.name}' successfully linked to factory '{factory.name}'")
                    else:
                        messages.error(request, "Failed to link device to factory")

            elif action == "remove_device_from_factory":
                with transaction.atomic():
                    device = Device.objects.select_for_update().get(id=device_id)
                    old_factory = device.factory
                    
                    # Force update to remove factory
                    Device.objects.filter(id=device_id).update(factory=None)
                    
                    # Verify the update
                    device.refresh_from_db()
                    if device.factory is None:
                        messages.success(request, f"Device '{device.name}' successfully unlinked from factory")
                    else:
                        messages.error(request, "Failed to unlink device from factory")

            elif action == "remove_factory":
                print("Action: Remove factory")
                factory = is_allowed_factory(request, factory_id)
                if not factory:
                    messages.error(request, "You are not allowed to remove this factory.")
                    return redirect("manage_factory")
                print(f"Factory found: {factory.name}. Removing now...")
                factory.delete()
                print("Factory removed successfully.")
                messages.success(request, _("Factory removed successfully."))

            elif action == "add_factory":
                print("Action: Add factory")
                factory_name = request.POST.get('factory_name')
                city_id = request.POST.get('city_id')
                print(f"Factory Name: {factory_name}, City ID: {city_id}")

                city = is_allowed_city(request, city_id)
                if not city:
                    messages.error(request, "You are not allowed to add factories to this city.")
                    return redirect("manage_factory")

                factory = Factory(name=factory_name)
                factory.city = city
                print(f"City found: {city.name}. Assigning to new factory.")
                factory.save()
                print(f"Factory '{factory_name}' has been added.")
                messages.success(request, f"Factory '{factory_name}' has been added.")

            elif action == "edit_factory":
                print("Action: Edit factory name")
                new_factory_name = request.POST.get('factory_name')
                factory = is_allowed_factory(request, factory_id)
                
                if not factory:
                    messages.error(request, "You are not allowed to edit this factory.")
                    return redirect("manage_factory")

                if not new_factory_name or new_factory_name.strip() == "":
                    messages.error(request, "Factory name cannot be empty.")
                    return redirect("manage_factory")

                print(f"Factory found: {factory.name}. Updating name to {new_factory_name}.")
                factory.name = new_factory_name.strip()
                factory.save()
                print(f"Factory name updated to '{new_factory_name}'.")
                messages.success(request, f"Factory name updated to '{new_factory_name}'.")

        except ObjectDoesNotExist as e:
            messages.error(request, f"Error: {str(e)}")
            print(f"Error occurred: {str(e)}")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")
            print(f"Unexpected error: {str(e)}")

        # Preserve search parameters in redirect
        redirect_url = "manage_factory"
        if search_query or city_filter:
            redirect_url += f"?search={search_query}&city_filter={city_filter}"
        return redirect(redirect_url)

    print("Rendering manage_factory template with cities and factories.")

    cities = allowed_cities(request)
    factories = allowed_factories(request)

    # Apply filters if they exist
    if search_query:
        factories = factories.filter(name__icontains=search_query)
    if city_filter:
        factories = factories.filter(city_id=city_filter)

    factory_data = [
        {
            'id': factory.id,
            'name': factory.name,
            'city': factory.city,
            'status': factory.status,
            'devices': Device.objects.filter(factory=factory)
        }
        for factory in factories
    ]
    
    # Add search parameters to template context
    context = {
        'factories': factory_data,
        'cities': cities,
        'search_query': search_query,
        'city_filter': city_filter,
    }
    
    return render(request, 'mill/manage_factory.html', context)