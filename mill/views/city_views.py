from django.shortcuts import render, redirect
from mill.models import City, Factory
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from mill.utils import allowed_cities
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from mill.utils import admin_required

def log_activity(user, obj, action_flag, change_message):
    """Helper function to log user activity"""
    try:
        # Get content type for the object
        content_type = ContentType.objects.get_for_model(City)
        
        # Create log entry
        LogEntry.objects.create(
            user_id=user.id,
            content_type_id=content_type.id,
            object_id=str(obj.id) if hasattr(obj, 'id') else '0',
            object_repr=str(obj),
            action_flag=action_flag,
            change_message=change_message,
            action_time=timezone.now()
        )
    except Exception as e:
        print(f"Error logging activity: {e}")
@admin_required
def manage_city(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        city_name = request.POST.get('city_name', '').strip()
        city_id = request.POST.get('city_id')

        print(f"Action: {action}, City Name: {city_name}, City ID: {city_id}")

        if action == 'add_city':
            if not city_name:
                messages.error(request, 'City name cannot be empty!')
                return redirect('manage_city')

            if City.objects.filter(name__iexact=city_name).exists():
                messages.error(request, 'City already exists!')
            else:
                try:
                    # Create new city
                    city = City.objects.create(name=city_name)
                    
                    # Log the creation
                    log_activity(
                        user=request.user,
                        obj=city,
                        action_flag=ADDITION,
                        change_message=f'Added new city "{city_name}"'
                    )
                    
                    messages.success(request, 'City added successfully!')
                except Exception as e:
                    print(f"Error adding city: {e}")
                    messages.error(request, 'Error adding city!')

        elif action == 'edit_city':
            if not city_name:
                messages.error(request, 'City name cannot be empty!')
                return redirect('manage_city')

            try:
                city = City.objects.get(id=city_id)
                old_name = city.name
                
                if old_name != city_name:  # Only update if name actually changed
                    city.name = city_name
                    city.save()
                    
                    # Log the change
                    log_activity(
                        user=request.user,
                        obj=city,
                        action_flag=CHANGE,
                        change_message=f'Changed city name from "{old_name}" to "{city_name}"'
                    )
                    
                    messages.success(request, 'City updated successfully!')
                
            except City.DoesNotExist:
                messages.error(request, 'City not found!')
            except Exception as e:
                print(f"Error updating city: {e}")
                messages.error(request, 'Error updating city!')

        elif action == 'remove_city':
            try:
                city = City.objects.get(id=city_id)
                city_name = city.name
                city_id = city.id  # Store ID before deletion
                
                # Log the deletion before actually deleting
                log_activity(
                    user=request.user,
                    obj=city,
                    action_flag=DELETION,
                    change_message=f'Deleted city "{city_name}"'
                )
                
                # Now delete the city
                city.delete()
                messages.success(request, 'City removed successfully!')
                
            except City.DoesNotExist:
                messages.error(request, 'City not found!')
            except Exception as e:
                print(f"Error removing city: {e}")
                messages.error(request, 'Error removing city!')

        return redirect('manage_city')

   # Handle GET request with search
    search_query = request.GET.get('search', '').strip()
    cities = allowed_cities(request)
    
    # Apply search filter if search query exists
    if search_query:
        cities = cities.filter(name__icontains=search_query)

    city_data = [
        {
            'id': city.id,
            'name': city.name,
            'factories_count': Factory.objects.filter(city=city).count()
        }
        for city in cities
    ]

    return render(request, 'mill/manage_city.html', {
        'cities': city_data,
    })
