from django.utils.translation import get_language
from django.shortcuts import render

def super_admin_view(request):
    current_locale = get_language()  # Gets the current language
    dir = 'rtl' if current_locale == 'ar' else 'ltr'
    return render(request, 'mill/super_admin.html', {'dir': dir, 'lang': current_locale})

def admin_view(request):
    # provide request.user as context
    context = {
        'user': request.user
    }
    return render(request, 'mill/admin.html', context)

def manage_admin_view(request):
    return render(request, 'mill/manage_admin.html')
