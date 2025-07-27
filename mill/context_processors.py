from django.utils.translation import get_language
from django.conf import settings

def language_context(request):
    """
    Context processor to provide language information to all templates
    """
    current_language = get_language()
    
    return {
        'current_language': current_language,
        'is_rtl': current_language == 'ar',
        'available_languages': settings.LANGUAGES,
        'language_direction': 'rtl' if current_language == 'ar' else 'ltr',
    } 