#!/usr/bin/env python3
"""
Test script to verify favicon and static logos are working correctly.
This script tests the changes made to implement TapNex favicon and static logos.
"""

import os
import sys
import django
from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

def test_static_files_exist():
    """Test that the required static logo files exist."""
    static_root = settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT
    
    # Test TapNex logo
    tapnex_logo_path = os.path.join(static_root, 'images', 'logos', 'TAPNEX_LOGO_BG.jpg')
    print(f"Checking TapNex logo: {tapnex_logo_path}")
    if os.path.exists(tapnex_logo_path):
        print("✅ TapNex logo file exists")
        print(f"   Size: {os.path.getsize(tapnex_logo_path)} bytes")
    else:
        print("❌ TapNex logo file NOT found")
    
    # Test NexGen logo
    nexgen_logo_path = os.path.join(static_root, 'images', 'logos', 'LOGO_NEXGEN_FC.png')
    print(f"Checking NexGen logo: {nexgen_logo_path}")
    if os.path.exists(nexgen_logo_path):
        print("✅ NexGen logo file exists")
        print(f"   Size: {os.path.getsize(nexgen_logo_path)} bytes")
    else:
        print("❌ NexGen logo file NOT found")

def test_templates_updated():
    """Test that templates have been updated with static file references."""
    templates_to_check = [
        'ticketing/templates/base.html',
        'templates/base.html',
        'ticketing/templates/core/home.html',
        'templates/animated_pass_template.html',
        'templates/404.html',
        'templates/403.html',
        'templates/400.html',
        'templates/500.html'
    ]
    
    for template_path in templates_to_check:
        full_path = os.path.join(settings.BASE_DIR, template_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for favicon
            if 'favicon' in content.lower():
                print(f"✅ {template_path} contains favicon references")
            
            # Check for static logo references
            if "{% static 'images/logos/TAPNEX_LOGO_BG.jpg' %}" in content:
                print(f"✅ {template_path} uses static TapNex logo")
            elif 'drive.google.com' in content and 'TAPNEX' in content:
                print(f"⚠️  {template_path} still contains Google Drive links")
            
            if "{% static 'images/logos/LOGO_NEXGEN_FC.png' %}" in content:
                print(f"✅ {template_path} uses static NexGen logo")
        else:
            print(f"❌ Template not found: {template_path}")

def main():
    """Run all tests."""
    print("🔍 Testing TapNex Favicon and Static Logo Implementation")
    print("=" * 60)
    
    print("\n📁 Testing Static Files...")
    test_static_files_exist()
    
    print("\n📄 Testing Template Updates...")
    test_templates_updated()
    
    print("\n" + "=" * 60)
    print("✅ Tests completed! Check output above for any issues.")
    print("\n💡 To verify in browser:")
    print("   1. Start the development server: python manage.py runserver")
    print("   2. Open your browser and check the favicon in the tab")
    print("   3. Visit the home page to see the updated logos")

if __name__ == "__main__":
    main()
