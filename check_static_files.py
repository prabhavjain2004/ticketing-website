#!/usr/bin/env python
"""
Script to check static files configuration for production
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')

import django
django.setup()

from django.conf import settings
from django.contrib.staticfiles.finders import find

def check_static_files():
    print("🔍 Checking Static Files Configuration...")
    print("=" * 50)
    
    # Check settings
    print(f"✅ STATIC_URL: {settings.STATIC_URL}")
    print(f"✅ STATIC_ROOT: {settings.STATIC_ROOT}")
    print(f"✅ STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
    print(f"✅ DEBUG: {settings.DEBUG}")
    print(f"✅ STATICFILES_STORAGE: {settings.STATICFILES_STORAGE}")
    
    # Check if static files exist
    print("\n📁 Checking Static Files...")
    
    # Test specific files
    test_files = [
        'core/images/TAPNEX_LOGO_BG.jpg',
        'core/images/LOGO_NEXGEN_FC.png',
        'css/event_pass.css',
        'js/ticket-functions.js'
    ]
    
    for file_path in test_files:
        found_path = find(file_path)
        if found_path:
            print(f"✅ Found: {file_path} -> {found_path}")
        else:
            print(f"❌ Missing: {file_path}")
    
    # Check STATIC_ROOT directory
    static_root = Path(settings.STATIC_ROOT)
    if static_root.exists():
        print(f"\n✅ STATIC_ROOT directory exists: {static_root}")
        static_files_count = len(list(static_root.rglob('*')))
        print(f"📊 Files in STATIC_ROOT: {static_files_count}")
    else:
        print(f"\n❌ STATIC_ROOT directory missing: {static_root}")
        print("💡 Run: python manage.py collectstatic --noinput")
    
    print("\n" + "=" * 50)
    print("🎯 Static Files Check Complete!")

if __name__ == "__main__":
    check_static_files()
