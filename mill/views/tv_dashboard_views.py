from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.urls import reverse
from ..models import TVDashboardSettings, City, Factory
from ..utils.permmissions_handler_utils import is_super_admin


@login_required
@user_passes_test(is_super_admin)
def tv_dashboard_settings_list(request):
    """List all TV dashboard settings"""
    settings_list = TVDashboardSettings.objects.all().order_by('-is_active', '-created_at')
    
    context = {
        'settings_list': settings_list,
        'active_config': TVDashboardSettings.get_active_config(),
    }
    return render(request, 'mill/tv_dashboard_settings_list.html', context)


@login_required
@user_passes_test(is_super_admin)
def tv_dashboard_settings_create(request):
    """Create a new TV dashboard setting"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Create the setting
                setting = TVDashboardSettings.objects.create(
                    name=request.POST.get('name'),
                    display_mode=request.POST.get('display_mode', 'all_factories'),
                    sort_criteria=request.POST.get('sort_criteria', 'daily_total'),
                    sort_direction=request.POST.get('sort_direction', 'desc'),
                    show_only_active=request.POST.get('show_only_active') == 'on',
                    show_summary_stats=request.POST.get('show_summary_stats') == 'on',
                    show_factory_status=request.POST.get('show_factory_status') == 'on',
                    show_time_info=request.POST.get('show_time_info') == 'on',
                    refresh_interval=int(request.POST.get('refresh_interval', 30)),
                    auto_scroll=request.POST.get('auto_scroll', 'none'),
                    scroll_speed=int(request.POST.get('scroll_speed', 120)),
                    cards_per_row=int(request.POST.get('cards_per_row', 3)),
                    show_city_headers=request.POST.get('show_city_headers') == 'on',
                    created_by=request.user
                )
                
                # Add selected cities
                selected_city_ids = request.POST.getlist('selected_cities')
                if selected_city_ids:
                    cities = City.objects.filter(id__in=selected_city_ids)
                    setting.selected_cities.set(cities)
                
                # Add selected factories
                selected_factory_ids = request.POST.getlist('selected_factories')
                if selected_factory_ids:
                    factories = Factory.objects.filter(id__in=selected_factory_ids)
                    setting.selected_factories.set(factories)
                
                # If this is set as active, deactivate others
                if request.POST.get('is_active') == 'on':
                    TVDashboardSettings.objects.exclude(id=setting.id).update(is_active=False)
                    setting.is_active = True
                    setting.save()
                
                messages.success(request, f'TV Dashboard setting "{setting.name}" created successfully!')
                return redirect('tv_dashboard_settings_list')
                
        except Exception as e:
            messages.error(request, f'Error creating TV dashboard setting: {str(e)}')
    
    # Get available cities and factories for the form
    cities = City.objects.filter(status=True).order_by('name')
    factories = Factory.objects.filter(status=True).order_by('name')
    
    context = {
        'cities': cities,
        'factories': factories,
        'display_modes': TVDashboardSettings.DISPLAY_MODES,
        'sort_criteria': TVDashboardSettings.SORT_CRITERIA,
        'refresh_intervals': TVDashboardSettings.REFRESH_INTERVALS,
        'auto_scroll_options': TVDashboardSettings.AUTO_SCROLL_OPTIONS,
    }
    return render(request, 'mill/tv_dashboard_settings_form.html', context)


@login_required
@user_passes_test(is_super_admin)
def tv_dashboard_settings_edit(request, setting_id):
    """Edit an existing TV dashboard setting"""
    setting = get_object_or_404(TVDashboardSettings, id=setting_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update basic fields
                setting.name = request.POST.get('name')
                setting.display_mode = request.POST.get('display_mode', 'all_factories')
                setting.sort_criteria = request.POST.get('sort_criteria', 'daily_total')
                setting.sort_direction = request.POST.get('sort_direction', 'desc')
                setting.show_only_active = request.POST.get('show_only_active') == 'on'
                setting.show_summary_stats = request.POST.get('show_summary_stats') == 'on'
                setting.show_factory_status = request.POST.get('show_factory_status') == 'on'
                setting.show_time_info = request.POST.get('show_time_info') == 'on'
                setting.refresh_interval = int(request.POST.get('refresh_interval', 30))
                setting.auto_scroll = request.POST.get('auto_scroll', 'none')
                setting.scroll_speed = int(request.POST.get('scroll_speed', 120))
                setting.cards_per_row = int(request.POST.get('cards_per_row', 3))
                setting.show_city_headers = request.POST.get('show_city_headers') == 'on'
                
                # Update selected cities
                selected_city_ids = request.POST.getlist('selected_cities')
                if selected_city_ids:
                    cities = City.objects.filter(id__in=selected_city_ids)
                    setting.selected_cities.set(cities)
                else:
                    setting.selected_cities.clear()
                
                # Update selected factories
                selected_factory_ids = request.POST.getlist('selected_factories')
                if selected_factory_ids:
                    factories = Factory.objects.filter(id__in=selected_factory_ids)
                    setting.selected_factories.set(factories)
                else:
                    setting.selected_factories.clear()
                
                # Handle active status
                is_active = request.POST.get('is_active') == 'on'
                if is_active and not setting.is_active:
                    # Deactivate other settings
                    TVDashboardSettings.objects.exclude(id=setting.id).update(is_active=False)
                setting.is_active = is_active
                
                setting.save()
                
                messages.success(request, f'TV Dashboard setting "{setting.name}" updated successfully!')
                return redirect('tv_dashboard_settings_list')
                
        except Exception as e:
            messages.error(request, f'Error updating TV dashboard setting: {str(e)}')
    
    # Get available cities and factories for the form
    cities = City.objects.filter(status=True).order_by('name')
    factories = Factory.objects.filter(status=True).order_by('name')
    
    context = {
        'setting': setting,
        'cities': cities,
        'factories': factories,
        'display_modes': TVDashboardSettings.DISPLAY_MODES,
        'sort_criteria': TVDashboardSettings.SORT_CRITERIA,
        'refresh_intervals': TVDashboardSettings.REFRESH_INTERVALS,
        'auto_scroll_options': TVDashboardSettings.AUTO_SCROLL_OPTIONS,
        'selected_city_ids': list(setting.selected_cities.values_list('id', flat=True)),
        'selected_factory_ids': list(setting.selected_factories.values_list('id', flat=True)),
    }
    return render(request, 'mill/tv_dashboard_settings_form.html', context)


@login_required
@user_passes_test(is_super_admin)
def tv_dashboard_settings_delete(request, setting_id):
    """Delete a TV dashboard setting"""
    setting = get_object_or_404(TVDashboardSettings, id=setting_id)
    
    if request.method == 'POST':
        try:
            setting_name = setting.name
            setting.delete()
            messages.success(request, f'TV Dashboard setting "{setting_name}" deleted successfully!')
            return redirect('tv_dashboard_settings_list')
        except Exception as e:
            messages.error(request, f'Error deleting TV dashboard setting: {str(e)}')
    
    context = {
        'setting': setting,
    }
    return render(request, 'mill/tv_dashboard_settings_confirm_delete.html', context)


@login_required
@user_passes_test(is_super_admin)
def tv_dashboard_settings_activate(request, setting_id):
    """Activate a TV dashboard setting"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Deactivate all settings
                TVDashboardSettings.objects.update(is_active=False)
                
                # Activate the selected setting
                setting = get_object_or_404(TVDashboardSettings, id=setting_id)
                setting.is_active = True
                setting.save()
                
                messages.success(request, f'TV Dashboard setting "{setting.name}" activated successfully!')
                return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid method'})


@login_required
@user_passes_test(is_super_admin)
def tv_dashboard_settings_preview(request, setting_id):
    """Preview a TV dashboard setting"""
    setting = get_object_or_404(TVDashboardSettings, id=setting_id)
    
    # Get the URL for this configuration
    preview_url = setting.get_display_url()
    
    context = {
        'setting': setting,
        'preview_url': preview_url,
    }
    return render(request, 'mill/tv_dashboard_settings_preview.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def tv_dashboard_settings_duplicate(request, setting_id):
    """Duplicate a TV dashboard setting"""
    if not request.user.is_authenticated or not is_super_admin(request.user):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'})
    
    try:
        original_setting = get_object_or_404(TVDashboardSettings, id=setting_id)
        
        with transaction.atomic():
            # Create a copy
            new_setting = TVDashboardSettings.objects.create(
                name=f"{original_setting.name} (Copy)",
                display_mode=original_setting.display_mode,
                sort_criteria=original_setting.sort_criteria,
                sort_direction=original_setting.sort_direction,
                show_only_active=original_setting.show_only_active,
                show_summary_stats=original_setting.show_summary_stats,
                show_factory_status=original_setting.show_factory_status,
                show_time_info=original_setting.show_time_info,
                refresh_interval=original_setting.refresh_interval,
                auto_scroll=original_setting.auto_scroll,
                scroll_speed=original_setting.scroll_speed,
                cards_per_row=original_setting.cards_per_row,
                show_city_headers=original_setting.show_city_headers,
                is_active=False,  # Duplicates are not active by default
                created_by=request.user
            )
            
            # Copy selected cities and factories
            new_setting.selected_cities.set(original_setting.selected_cities.all())
            new_setting.selected_factories.set(original_setting.selected_factories.all())
            
            return JsonResponse({
                'status': 'success',
                'message': f'Setting "{original_setting.name}" duplicated successfully!',
                'new_setting_id': new_setting.id
            })
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}) 