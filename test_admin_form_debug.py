#!/usr/bin/env python3
"""
Test script to debug the sponsor form functionality in the admin dashboard.
This script helps identify any JavaScript or form structure issues.
"""

import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.forms import formset_factory
from ticketing.models import Event, Sponsor
from ticketing.forms import EventForm, SponsorForm

User = get_user_model()

def test_admin_form_functionality():
    """Test the admin form functionality and identify potential issues."""
    
    print("🔍 Testing Admin Form Functionality")
    print("=" * 50)
    
    # Create test client and admin user
    client = Client()
    
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='testadmin',
                email='admin@test.com',
                password='testpass123'
            )
            print(f"✅ Created admin user: {admin_user.username}")
        else:
            print(f"✅ Using existing admin user: {admin_user.username}")
        
        # Login as admin
        client.force_login(admin_user)
        
        # Test event creation form access
        print("\n📝 Testing Event Creation Form Access:")
        response = client.get('/admin/events/create/')
        print(f"   - Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   - ✅ Form accessible")
            
            # Check if sponsor formset is in context
            if 'sponsor_formset' in response.context:
                formset = response.context['sponsor_formset']
                print(f"   - ✅ Sponsor formset found with {len(formset.forms)} forms")
                print(f"   - Management form: {formset.management_form}")
                
                # Check individual forms
                for i, form in enumerate(formset.forms):
                    print(f"   - Form {i}: {form.fields.keys()}")
                    if hasattr(form, 'instance') and form.instance.pk:
                        print(f"     Instance: {form.instance}")
                    else:
                        print(f"     New form (no instance)")
            else:
                print("   - ❌ Sponsor formset not found in context")
                
            # Check for specific template content
            content = response.content.decode('utf-8')
            
            checks = [
                ('sponsors-container', 'Sponsors container div'),
                ('add-sponsor-btn', 'Add sponsor button'),
                ('sponsor-embed-input', 'Iframe input field'),
                ('test-sponsor-url', 'Test URL button'),
                ('processEmbedInput', 'Iframe processing function'),
                ('extractUrlFromInput', 'URL extraction function'),
                ('validateGoogleDriveUrl', 'URL validation function'),
            ]
            
            print("\n🔍 Template Content Checks:")
            for check_id, description in checks:
                if check_id in content:
                    print(f"   - ✅ {description} found")
                else:
                    print(f"   - ❌ {description} missing")
                    
        else:
            print(f"   - ❌ Form not accessible (Status: {response.status_code})")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        
    # Test sponsor form structure
    print("\n📋 Testing Sponsor Form Structure:")
    try:
        SponsorFormSet = formset_factory(SponsorForm, extra=1)
        formset = SponsorFormSet()
        
        print(f"   - ✅ Formset created successfully")
        print(f"   - Total forms: {formset.total_form_count()}")
        print(f"   - Management form: {formset.management_form}")
        
        # Check first form fields
        if formset.forms:
            first_form = formset.forms[0]
            print(f"   - Form fields: {list(first_form.fields.keys())}")
            
            # Check specific field configurations
            fields_to_check = ['sponsor_name', 'logo_url', 'website_url', 'sponsor_type', 'order']
            for field_name in fields_to_check:
                if field_name in first_form.fields:
                    field = first_form.fields[field_name]
                    print(f"     - {field_name}: required={field.required}, widget={type(field.widget).__name__}")
                else:
                    print(f"     - ❌ {field_name} field missing")
                    
    except Exception as e:
        print(f"❌ Error testing sponsor form: {e}")
        
    print("\n🔧 Suggested Debugging Steps:")
    print("   1. Check browser console for JavaScript errors")
    print("   2. Verify Django form field IDs match JavaScript selectors")
    print("   3. Test iframe parsing with sample Google Drive URLs")
    print("   4. Ensure formset management form is properly rendered")
    print("   5. Check if CSS classes are correctly applied")
    
    print("\n📊 Test Complete!")

if __name__ == "__main__":
    test_admin_form_functionality()
