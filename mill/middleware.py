from django.shortcuts import redirect
from django.urls import resolve
from django.core.exceptions import PermissionDenied

class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        protected_paths = [
            '/manage-devices/',
            '/admin/',
            '/super-admin/',
            '/manage-factory/',
            '/manage-city/',
            '/manage-users/',
        ]

        if any(path.startswith(p) for p in protected_paths):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # SuperAdmin paths
            if path.startswith('/super-admin/'):
                if not (request.user.groups.filter(name='Superadmin').exists() or request.user.is_superuser):
                    raise PermissionDenied
            
            # Admin paths
            elif path.startswith(('/admin/', '/manage-')):
                if not (request.user.groups.filter(name__in=['Admin', 'Superadmin']).exists() or request.user.is_superuser):
                    raise PermissionDenied

        response = self.get_response(request)
        return response