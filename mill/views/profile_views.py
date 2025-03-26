from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from .profile_form import UserUpdateForm, CustomPasswordChangeForm

@login_required
def manage_profile(request):
    user = request.user
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, f'Profile updated successfully on {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
                return redirect('manage_profile')
            else:
                messages.error(request, 'Please correct the errors below.')
        
        elif 'change_password' in request.POST:
            password_form = CustomPasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, 'Your password was successfully updated!')
                return redirect('manage_profile')
            else:
                messages.error(request, 'Please correct the errors in the password form.')
    else:
        user_form = UserUpdateForm(instance=user)
        password_form = CustomPasswordChangeForm(user)

    context = {
        'user_form': user_form,
        'password_form': password_form,
        'last_update': timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        'current_user': user.username
    }
    return render(request, 'accounts/manage_profile.html', context)