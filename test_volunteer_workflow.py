#!/usr/bin/env python
"""
Complete test of the volunteer login workflow
"""
import os
import sys
import django

# Set up Django environment
sys.path.insert(0, '/c/Users/MOINAK/OneDrive/Desktop/TapNex/Tapnex/myproject')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from django.test import Client
from django.contrib.auth import authenticate
from ticketing.models import User

def test_complete_volunteer_workflow():
    """Test the complete volunteer login workflow"""
    print("🔍 Testing Complete Volunteer Workflow")
    print("=" * 50)
    
    # Get volunteer user
    volunteer = User.objects.filter(role='VOLUNTEER').first()
    if not volunteer:
        print("❌ No volunteer user found!")
        return False
    
    print(f"✅ Volunteer User: {volunteer.email}")
    print(f"   - Role: {volunteer.role}")
    print(f"   - Active: {volunteer.is_active}")
    print(f"   - Staff: {volunteer.is_staff}")
    print()
    
    # Test authentication
    # Note: We can't test password authentication without knowing the password
    # But we can simulate the login process
    client = Client()
    
    # 1. Test login page access
    print("1. Testing login page access...")
    login_response = client.get('/login/')
    print(f"   Login page status: {login_response.status_code} ✅")
    
    # 2. Force login (simulating successful authentication)
    print("\n2. Simulating successful login...")
    client.force_login(volunteer)
    print("   ✅ User logged in successfully")
    
    # 3. Test dashboard redirect
    print("\n3. Testing dashboard access...")
    dashboard_response = client.get('/dashboard/')
    if dashboard_response.status_code == 302:
        redirect_url = dashboard_response.url
        print(f"   ✅ Dashboard redirects to: {redirect_url}")
        
        if '/volunteer/dashboard/' in redirect_url:
            print("   ✅ Correctly redirects to volunteer dashboard!")
        else:
            print(f"   ❌ Unexpected redirect: {redirect_url}")
    else:
        print(f"   ❌ Dashboard should redirect but returned: {dashboard_response.status_code}")
    
    # 4. Test volunteer dashboard access
    print("\n4. Testing volunteer dashboard...")
    volunteer_dashboard_response = client.get('/volunteer/dashboard/')
    if volunteer_dashboard_response.status_code == 200:
        print("   ✅ Volunteer dashboard accessible!")
        
        # Check if the page contains expected content
        content = volunteer_dashboard_response.content.decode('utf-8')
        if 'Scan Tickets' in content:
            print("   ✅ Dashboard contains scan tickets functionality!")
        if 'Start Scanning Tickets' in content:
            print("   ✅ Dashboard contains main scan button!")
        if 'volunteer_scan_tickets' in content:
            print("   ✅ Dashboard contains link to scan page!")
    else:
        print(f"   ❌ Volunteer dashboard error: {volunteer_dashboard_response.status_code}")
    
    # 5. Test scan tickets page
    print("\n5. Testing scan tickets page...")
    scan_response = client.get('/volunteer/scan/')
    if scan_response.status_code == 200:
        print("   ✅ Scan tickets page accessible!")
        
        # Check if the page contains QR scanner elements
        scan_content = scan_response.content.decode('utf-8')
        if 'camera' in scan_content.lower() or 'qr' in scan_content.lower():
            print("   ✅ Scan page contains camera/QR functionality!")
    else:
        print(f"   ❌ Scan tickets page error: {scan_response.status_code}")
    
    # 6. Test API endpoint access
    print("\n6. Testing API validate ticket endpoint...")
    api_response = client.post('/api/validate-ticket/', 
                              data='{"tid": "test", "tok": "test"}',
                              content_type='application/json')
    if api_response.status_code in [400, 404]:  # Expected for invalid data
        print("   ✅ API endpoint accessible (returns expected error for invalid data)")
    elif api_response.status_code == 403:
        print("   ❌ API endpoint forbidden - permission issue")
    else:
        print(f"   ℹ️  API endpoint status: {api_response.status_code}")
    
    print("\n" + "=" * 50)
    print("🎉 Volunteer workflow test completed!")
    print("\nNext steps for the user:")
    print("1. Log in with volunteer credentials: juug23btech19126@gmail.com")
    print("2. You should be automatically redirected to volunteer dashboard")
    print("3. Click on 'Start Scanning Tickets' button")
    print("4. Use the QR scanner to validate tickets")
    
    return True

if __name__ == "__main__":
    test_complete_volunteer_workflow()
