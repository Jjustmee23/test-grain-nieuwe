from django.shortcuts import redirect
from django.urls import resolve
from django.core.exceptions import PermissionDenied
from django.utils.translation import activate, get_language
from django.conf import settings

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

class LanguageMiddleware:
    """
    Middleware to handle language detection and RTL support
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check for language parameter in URL
        lang_param = request.GET.get('lang')
        if lang_param and lang_param in [lang[0] for lang in settings.LANGUAGES]:
            activate(lang_param)
            request.session['django_language'] = lang_param
        
        # Check session for saved language
        elif 'django_language' in request.session:
            activate(request.session['django_language'])
        
        # Check Accept-Language header
        else:
            accept_lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            if accept_lang:
                # Parse Accept-Language header
                for lang in accept_lang.split(','):
                    lang_code = lang.split(';')[0].strip()
                    # Check if it's a supported language
                    if lang_code in [lang[0] for lang in settings.LANGUAGES]:
                        activate(lang_code)
                        request.session['django_language'] = lang_code
                        break
                    # Check for language variants (e.g., ar-EG -> ar)
                    elif '-' in lang_code:
                        base_lang = lang_code.split('-')[0]
                        if base_lang in [lang[0] for lang in settings.LANGUAGES]:
                            activate(base_lang)
                            request.session['django_language'] = base_lang
                            break

        # Add language info to request
        request.current_language = get_language()
        request.is_rtl = request.current_language == 'ar'
        
        response = self.get_response(request)
        return response