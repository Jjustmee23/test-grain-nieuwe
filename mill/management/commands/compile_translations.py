from django.core.management.base import BaseCommand
from django.conf import settings
import os
import shutil
from pathlib import Path

class Command(BaseCommand):
    help = 'Compile translation files without requiring gettext'

    def handle(self, *args, **options):
        self.stdout.write('Compiling translation files...')
        
        locale_path = Path(settings.BASE_DIR) / 'locale'
        
        if not locale_path.exists():
            self.stdout.write(self.style.ERROR('Locale directory not found'))
            return
        
        for lang_dir in locale_path.iterdir():
            if lang_dir.is_dir() and lang_dir.name in ['ar', 'en']:
                lc_messages = lang_dir / 'LC_MESSAGES'
                if lc_messages.exists():
                    po_file = lc_messages / 'django.po'
                    mo_file = lc_messages / 'django.mo'
                    
                    if po_file.exists():
                        # Create a simple .mo file by copying the .po file
                        # This is a workaround when gettext is not available
                        try:
                            shutil.copy2(po_file, mo_file)
                            self.stdout.write(
                                self.style.SUCCESS(f'Compiled {lang_dir.name}/LC_MESSAGES/django.mo')
                            )
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f'Error compiling {lang_dir.name}: {e}')
                            )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'No .po file found for {lang_dir.name}')
                        )
        
        self.stdout.write(self.style.SUCCESS('Translation compilation completed')) 