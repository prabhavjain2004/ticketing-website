from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.staticfiles import finders
import os

class Command(BaseCommand):
    help = 'Check if static files exist and are accessible'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Checking Static Files...'))
        
        # Files to check
        files_to_check = [
            'images/logos/TAPNEX_LOGO_BG.jpg',
            'images/logos/LOGO_NEXGEN_FC.png',
        ]
        
        for file_path in files_to_check:
            self.stdout.write(f'\nChecking: {file_path}')
            
            # Try to find the file
            found_path = finders.find(file_path)
            
            if found_path:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ Found at: {found_path}')
                )
                
                # Check if file actually exists
                if os.path.exists(found_path):
                    file_size = os.path.getsize(found_path)
                    self.stdout.write(
                        self.style.SUCCESS(f'  📁 File size: {file_size} bytes')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ File path exists but file not found')
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Not found in any static directories')
                )
        
        # Check static directories
        self.stdout.write(f'\n📂 Static Directories:')
        for directory in settings.STATICFILES_DIRS:
            if os.path.exists(directory):
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ {directory}')
                )
                
                # Check if logos directory exists
                logos_dir = os.path.join(directory, 'images', 'logos')
                if os.path.exists(logos_dir):
                    self.stdout.write(
                        self.style.SUCCESS(f'    ✅ {logos_dir}')
                    )
                    # List files in logos directory
                    try:
                        files = os.listdir(logos_dir)
                        for file in files:
                            file_path = os.path.join(logos_dir, file)
                            if os.path.isfile(file_path):
                                file_size = os.path.getsize(file_path)
                                self.stdout.write(
                                    self.style.SUCCESS(f'      📄 {file} ({file_size} bytes)')
                                )
                    except OSError as e:
                        self.stdout.write(
                            self.style.ERROR(f'    ❌ Cannot list files: {e}')
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'    ⚠️  {logos_dir} (not found)')
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ {directory} (not found)')
                )
        
        self.stdout.write(f'\n📁 Static Root: {settings.STATIC_ROOT}')
        self.stdout.write(f'🔗 Static URL: {settings.STATIC_URL}')
        
        # Check if static root has logos
        if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
            static_logos_dir = os.path.join(settings.STATIC_ROOT, 'images', 'logos')
            if os.path.exists(static_logos_dir):
                self.stdout.write(f'\n✅ Static root logos directory exists: {static_logos_dir}')
                try:
                    files = os.listdir(static_logos_dir)
                    for file in files:
                        file_path = os.path.join(static_logos_dir, file)
                        if os.path.isfile(file_path):
                            file_size = os.path.getsize(file_path)
                            self.stdout.write(
                                self.style.SUCCESS(f'  📄 {file} ({file_size} bytes)')
                            )
                except OSError as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Cannot list static root files: {e}')
                    )
            else:
                self.stdout.write(f'\n⚠️  Static root logos directory not found: {static_logos_dir}')
