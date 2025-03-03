from django.utils.translation import get_language
from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def super_admin_view(request):
    current_locale = get_language()  # Gets the current language
    dir = 'rtl' if current_locale == 'ar' else 'ltr'
    return render(request, 'mill/super_admin.html', {'dir': dir, 'lang': current_locale})

def admin_view(request):
    context = {
        'user': request.user
    }
    return render(request, 'mill/admin.html', context)

def manage_admin_view(request):
    return render(request, 'mill/manage_admin.html')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('dashboard')  # Changed from 'admin_view' to 'dashboard'
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'user': request.user
    }
    return render(request, 'mill/change_password.html', context)