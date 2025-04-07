from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.models import Group, User
from mill.forms import CustomUserCreationForm, UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from mill.models import UserProfile

# Authentication Views
class BasicLoginView(LoginView):
    template_name = 'mill/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('index')  # Redirect to 'index' view after successful login

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        else:
            return self.success_url

class BasicLogoutView(LogoutView):
    next_page = reverse_lazy('login')  # Redirect to 'login' after logout

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the user to the database
            login(request, user)  # Log in the user after registration
            # Assign the 'user' group to the new user
            user_group = Group.objects.get(name='user')
            user.groups.add(user_group)
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'mill/register.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'mill/profile.html')
@login_required
def manage_users(request):
    # Get all users who are NOT superusers and NOT in the Superadmin group
    users = User.objects.exclude(is_superuser=True).exclude(groups__name='Superadmin').exclude(groups__name='Admin')
    return render(request, 'mill/manage_users.html', {'users': users})


# Create new user view
@login_required
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

# Edit existing user view
@login_required
def edit_user(request, user_id):
    pass
#     user = get_object_or_404(User, id=user_id)
#     if request.method == 'POST':
#         form = UserChangeForm(request.POST, instance=user)
#         if form.is_valid():
#             form.save()
#             return redirect('manage_users')
#     else:
#         form = UserChangeForm(instance=user)
#     return render(request, 'mill/edit_user.html', {'form': form, 'user': user})

# Delete user view
@login_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        
        return redirect('manage_users')
    return render(request, 'mill/delete_user.html', {'user': user})

# Assign permissions/rights to a user (e.g., add to group)
@login_required
def assign_rights(request, user_id):
    user = get_object_or_404(User, id=user_id)
    groups = Group.objects.all()  # Get all available groups (roles)
    
    if request.method == 'POST':
        selected_group = request.POST.get('group')
        group = Group.objects.get(name=selected_group)
        user.groups.add(group)
        return redirect('manage_users')

    return render(request, 'mill/assign_rights.html', {'user': user, 'groups': groups})

