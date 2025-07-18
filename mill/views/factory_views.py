from django.shortcuts import render, get_object_or_404, redirect
# from django.http import JsonResponse
from mill.models import Factory, City, Device
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from mill.utils import allowed_cities, allowed_factories, is_allowed_city, is_allowed_factory
from django.utils.translation import gettext as _
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from mill.utils import admin_required

def log_activity(user, obj, action_flag, change_message):
    """Helper function to log user activity"""
    try:
        content_type = ContentType.objects.get_for_model(obj)
        LogEntry.objects.create(
            user_id=user.id,
            content_type_id=content_type.id,
            object_id=str(obj.id),
            object_repr=str(obj),
            action_flag=action_flag,
            change_message=change_message,
            action_time=timezone.now()
        )
    except Exception as e:
        print(f"Error logging activity: {e}")
        
@admin_required
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
                    
                    old_factory = device.factory
                    Device.objects.filter(id=device_id).update(factory=factory)
                    device.refresh_from_db()
                    
                    if device.factory == factory:
                        messages.success(request, f"Device '{device.name}' successfully linked to factory '{factory.name}'")
                        # Log device linking
                        log_activity(
                            user=request.user,
                            obj=device,
                            action_flag=CHANGE,
                            change_message=f"Linked device '{device.name}' to factory '{factory.name}'"
                        )
                    else:
                        messages.error(request, "Failed to link device to factory")

            elif action == "remove_device_from_factory":
                with transaction.atomic():
                    device = Device.objects.select_for_update().get(id=device_id)
                    old_factory = device.factory
                    
                    if old_factory:  # Only log if device was actually linked to a factory
                        old_factory_name = old_factory.name
                        Device.objects.filter(id=device_id).update(factory=None)
                        device.refresh_from_db()
                        
                        if device.factory is None:
                            messages.success(request, f"Device '{device.name}' successfully unlinked from factory")
                            # Log device unlinking
                            log_activity(
                                user=request.user,
                                obj=device,
                                action_flag=CHANGE,
                                change_message=f"Unlinked device '{device.name}' from factory '{old_factory_name}'"
                            )
                        else:
                            messages.error(request, "Failed to unlink device from factory")

            elif action == "remove_factory":
                factory = is_allowed_factory(request, factory_id)
                if not factory:
                    messages.error(request, "You are not allowed to remove this factory.")
                    return redirect("manage_factory")
                
                factory_name = factory.name
                # Log factory deletion before deleting
                log_activity(
                    user=request.user,
                    obj=factory,
                    action_flag=DELETION,
                    change_message=f"Deleted factory '{factory_name}'"
                )
                
                factory.delete()
                messages.success(request, _("Factory removed successfully."))

            elif action == "add_factory":
                factory_name = request.POST.get('factory_name')
                city_id = request.POST.get('city_id')
                group = request.POST.get('group', 'public')  # Default to 'public' if not provided

                city = is_allowed_city(request, city_id)
                if not city:
                    messages.error(request, "You are not allowed to add factories to this city.")
                    return redirect("manage_factory")

                factory = Factory(name=factory_name)
                factory.city = city
                factory.group = group
                factory.save()
                
                # Log factory creation
                log_activity(
                    user=request.user,
                    obj=factory,
                    action_flag=ADDITION,
                    change_message=f"Created new factory '{factory_name}' in city '{city.name}' with sector '{group}'"
                )
                
                messages.success(request, f"Factory '{factory_name}' has been added.")

            elif action == "edit_factory":
                print("Action: Edit factory")
                new_factory_name = request.POST.get('factory_name')
                new_group = request.POST.get('group')
                factory = is_allowed_factory(request, factory_id)
                
                if not factory:
                    messages.error(request, "You are not allowed to edit this factory.")
                    return redirect("manage_factory")

                if not new_factory_name or new_factory_name.strip() == "":
                    messages.error(request, "Factory name cannot be empty.")
                    return redirect("manage_factory")

                print(f"Factory found: {factory.name}. Updating name to {new_factory_name} and sector to {new_group}.")
                factory.name = new_factory_name.strip()
                
                # Update group/sector if provided
                if new_group:
                    factory.group = new_group
                
                factory.save()
                print(f"Factory updated: name='{new_factory_name}', sector='{factory.group}'.")
                messages.success(request, f"Factory updated: '{new_factory_name}' (Sector: {factory.group})")

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
            'group': factory.group,  # Add the group/sector
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

