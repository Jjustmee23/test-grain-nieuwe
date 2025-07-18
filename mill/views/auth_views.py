from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from mill.forms import CustomUserCreationForm, UserCreationForm
from mill.models import UserProfile

def superadmin_required(function):
    def wrap(request, *args, **kwargs):
        if request.user.groups.filter(name='Superadmin').exists():
            return function(request, *args, **kwargs)
        raise PermissionDenied
    return wrap

def admin_required(function):
    def wrap(request, *args, **kwargs):
        if request.user.groups.filter(name__in=['Admin', 'Superadmin']).exists():
            return function(request, *args, **kwargs)
        raise PermissionDenied
    return wrap

class BasicLoginView(LoginView):
    template_name = 'mill/login.html'
    success_url = reverse_lazy('dashboard')

    def get_success_url(self):
        return reverse_lazy('dashboard')

class BasicLogoutView(LogoutView):
    next_page = reverse_lazy('login')

@login_required
def profile(request):
    return render(request, 'mill/profile.html')

@login_required
def manage_profile(request):
    if request.method == 'POST':
        # Handle profile update logic here
        pass
    return render(request, 'mill/manage_profile.html')

@login_required
def change_password(request):
    if request.method == 'POST':
        # Handle password change logic here
        pass
    return render(request, 'mill/change_password.html')

@login_required
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'mill/register.html', {'form': form})

@superadmin_required
def manage_users(request):
    # Get all users who are NOT superusers and NOT in the Superadmin group
    users = User.objects.exclude(is_superuser=True).exclude(groups__name='Superadmin').exclude(groups__name='Admin')
    return render(request, 'mill/manage_users.html', {'users': users})

@superadmin_required
def create_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            print("Form is valid")
            new_user = form.save()
            creater_profile = UserProfile.objects.get(user=request.user)
            # Create a UserProfile entry for the new user
            new_user_profile = UserProfile.objects.create(
                user=new_user,
                team=request.user.username,
            )
            new_user_profile.allowed_cities.set(creater_profile.allowed_cities.all())
            new_user_profile.allowed_factories.set(creater_profile.allowed_factories.all())
            new_user_profile.save()
            messages.success(request, f"User created {new_user.username}")
        else:
            print("Form is invalid")
            messages.error(request, 'Please correct the error below.')
        return redirect('manage_users')
        
    else:
        form = UserCreationForm()
    return render(request, 'mill/create_user.html', {'form': form})

@superadmin_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        # Handle user edit logic here
        pass
    return render(request, 'mill/edit_user.html', {'user': user})

@superadmin_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('manage_users')
    return render(request, 'mill/delete_user.html', {'user': user})

# Assign permissions/rights to a user (e.g., add to group)
@superadmin_required
def assign_rights(request, user_id):
    user = get_object_or_404(User, id=user_id)
    groups = Group.objects.all()  # Get all available groups (roles)
    
    if request.method == 'POST':
        selected_group = request.POST.get('group')
        group = Group.objects.get(name=selected_group)
        user.groups.add(group)
        return redirect('manage_users')

    return render(request, 'mill/assign_rights.html', {'user': user, 'groups': groups})

