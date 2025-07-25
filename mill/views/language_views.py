from django.shortcuts import redirect
from django.utils.translation import activate, get_language
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json

def set_language(request):
    """
    View to handle language switching
    """
    if request.method == 'POST':
        language = request.POST.get('language')
        if language:
            # Activate the selected language
            activate(language)
            # Store in session
            request.session['django_language'] = language
            # Redirect back to the same page or referer
            next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'
            return redirect(next_url)
    
    # If GET request, redirect to home
    return redirect('/')

@csrf_exempt
@require_POST
def ajax_set_language(request):
    """
    AJAX endpoint for language switching
    """
    try:
        data = json.loads(request.body)
        language = data.get('language')
        
        if language:
            activate(language)
            request.session['django_language'] = language
            return JsonResponse({'status': 'success', 'language': language})
        else:
            return JsonResponse({'status': 'error', 'message': 'No language specified'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'})

def get_current_language(request):
    """
    Get current language information
    """
    current_lang = get_language()
    return JsonResponse({
        'current_language': current_lang,
        'is_rtl': current_lang == 'ar'
    })

def language_test(request):
    """
    Test page for language functionality
    """
    return render(request, 'mill/language_test.html') 