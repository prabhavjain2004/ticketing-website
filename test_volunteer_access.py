#!/usr/bin/env python
"""
Test script to verify volunteer dashboard access
"""
import os
import sys
import django

# Add the project root to the path
sys.path.insert(0, '/c/Users/MOINAK/OneDrive/Desktop/TapNex/Tapnex/myproject')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from django.test import Client
from ticketing.models import User

def test_volunteer_access():
    """Test volunteer dashboard access"""
    client = Client()
    
    # Get volunteer user
    volunteer = User.objects.filter(role='VOLUNTEER').first()
    if not volunteer:
        print("❌ No volunteer user found!")
        return False
    
    print(f"✅ Found volunteer: {volunteer.email}")
    
    # Force login the volunteer
    client.force_login(volunteer)
    
    # Test direct volunteer dashboard access
    response = client.get('/volunteer/dashboard/')
    print(f"Volunteer dashboard (/volunteer/dashboard/): {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Volunteer dashboard accessible!")
    else:
        print(f"❌ Volunteer dashboard error: {response.status_code}")
        if hasattr(response, 'content'):
            print(f"Error content: {response.content[:200]}")
    
    # Test main dashboard redirect
    response2 = client.get('/dashboard/')
    print(f"Main dashboard (/dashboard/): {response2.status_code}")
    
    if response2.status_code == 302:  # Redirect
        print(f"✅ Dashboard redirects to: {response2.url}")
    elif response2.status_code == 200:
        print("❌ Dashboard should redirect volunteers but returned 200")
    else:
        print(f"❌ Dashboard error: {response2.status_code}")
    
    # Test scan tickets page
    response3 = client.get('/volunteer/scan/')
    print(f"Scan tickets page (/volunteer/scan/): {response3.status_code}")
    
    if response3.status_code == 200:
        print("✅ Scan tickets page accessible!")
    else:
        print(f"❌ Scan tickets page error: {response3.status_code}")
    
    return True

if __name__ == "__main__":
    test_volunteer_access()
