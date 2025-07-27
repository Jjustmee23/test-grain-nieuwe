// Language switching functionality
document.addEventListener('DOMContentLoaded', function() {
    
    // Language switcher functionality
    const languageSwitcher = document.querySelector('.language-switcher');
    if (languageSwitcher) {
        const languageButtons = languageSwitcher.querySelectorAll('.dropdown-item');
        
        languageButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                const form = this.closest('form');
                if (form) {
                    // Show loading state
                    this.innerHTML = '<i class="bi bi-arrow-clockwise spin"></i> Loading...';
                    this.disabled = true;
                    
                    // Submit form
                    form.submit();
                }
            });
        });
    }
    
    // AJAX language switching (alternative method)
    function switchLanguageAjax(language) {
        fetch('/ajax-set-language/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                language: language
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Reload page to apply new language
                window.location.reload();
            } else {
                console.error('Language switch failed:', data.message);
            }
        })
        .catch(error => {
            console.error('Error switching language:', error);
        });
    }
    
    // Get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // RTL text direction detection
    function updateTextDirection() {
        const html = document.documentElement;
        const currentLang = html.getAttribute('lang');
        
        if (currentLang === 'ar') {
            html.setAttribute('dir', 'rtl');
            document.body.classList.add('rtl');
        } else {
            html.setAttribute('dir', 'ltr');
            document.body.classList.remove('rtl');
        }
    }
    
    // Initialize text direction
    updateTextDirection();
    
    // Add RTL-specific styles dynamically
    function addRTLStyles() {
        if (document.documentElement.getAttribute('dir') === 'rtl') {
            // Add any additional RTL-specific JavaScript functionality here
            console.log('RTL mode activated');
        }
    }
    
    addRTLStyles();
    
    // Language detection from browser
    function detectBrowserLanguage() {
        const browserLang = navigator.language || navigator.userLanguage;
        const supportedLanguages = ['ar', 'en'];
        
        // Check if browser language is supported
        for (let lang of supportedLanguages) {
            if (browserLang.startsWith(lang)) {
                return lang;
            }
        }
        
        return 'ar'; // Default to Arabic
    }
    
    // Auto-switch language based on browser preference (optional)
    function autoSwitchLanguage() {
        const currentLang = document.documentElement.getAttribute('lang');
        const browserLang = detectBrowserLanguage();
        
        if (currentLang !== browserLang) {
            // Only auto-switch if user hasn't manually set a preference
            if (!localStorage.getItem('userLanguagePreference')) {
                switchLanguageAjax(browserLang);
            }
        }
    }
    
    // Store user language preference
    function storeLanguagePreference(language) {
        localStorage.setItem('userLanguagePreference', language);
    }
    
    // Expose functions globally for use in other scripts
    window.LanguageManager = {
        switchLanguage: switchLanguageAjax,
        detectBrowserLanguage: detectBrowserLanguage,
        storeLanguagePreference: storeLanguagePreference,
        updateTextDirection: updateTextDirection
    };
});

// Add CSS for loading spinner
const style = document.createElement('style');
style.textContent = `
    .spin {
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .rtl {
        direction: rtl;
        text-align: right;
    }
    
    .rtl .dropdown-menu {
        right: 0;
        left: auto;
    }
    
    .rtl .navbar-nav {
        padding-right: 0;
    }
    
    .rtl .btn i {
        margin-right: 0;
        margin-left: 0.5rem;
    }
`;
document.head.appendChild(style); 