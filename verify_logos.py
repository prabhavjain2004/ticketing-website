#!/usr/bin/env python
"""
Quick verification script for static files paths
"""
import os
import django
from django.conf import settings
from django.templatetags.static import static

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

def verify_logos():
    print("🔍 Verifying Logo Static Files...")
    print("=" * 50)
    
    # Check settings
    print(f"DEBUG: {settings.DEBUG}")
    print(f"STATIC_URL: {settings.STATIC_URL}")
    print(f"STATIC_ROOT: {settings.STATIC_ROOT}")
    
    # Check logo paths
    logos = [
        'images/logos/TAPNEX_LOGO_BG.jpg',
        'images/logos/LOGO_NEXGEN_FC.png'
    ]
    
    for logo in logos:
        static_url = static(logo)
        print(f"\n📁 {logo}")
        print(f"   Static URL: {static_url}")
        
        # Check if file exists in staticfiles_build
        static_file_path = os.path.join(settings.STATIC_ROOT, logo)
        exists = os.path.exists(static_file_path)
        print(f"   File exists: {'✅' if exists else '❌'} {static_file_path}")
        
        if exists:
            file_size = os.path.getsize(static_file_path)
            print(f"   File size: {file_size} bytes")

if __name__ == "__main__":
    verify_logos()
