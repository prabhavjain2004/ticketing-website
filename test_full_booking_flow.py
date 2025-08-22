#!/usr/bin/env python3
"""
Test script to simulate the complete user booking flow and identify the 401 error.
"""

import os
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

def test_full_booking_flow():
    """Test the complete booking flow to identify where the 401 error occurs"""
    
    print("=== Testing Full Booking Flow ===")
    
    # Create a test client
    client = Client()
    
    # Get the correct User model
    User = get_user_model()
    
    # Step 1: Create a test user
    try:
        user = User.objects.get(username='testuser')
        print("✅ Using existing test user")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        print("✅ Created new test user")
    
    # Step 2: Login the user
    login_success = client.login(username='testuser', password='testpass123')
    if login_success:
        print("✅ User logged in successfully")
    else:
        print("❌ Failed to login user")
        return False
    
    # Step 3: Set up ticket order in session (simulate booking flow)
    session = client.session
    session['ticket_order'] = {
        'event_id': 7,  # Assuming event 7 exists
        'tickets': [{'category': 'General', 'quantity': 1, 'price': 51.0}],
        'subtotal': 51.0,
        'total': 51.0,
        'total_attendees': 1
    }
    session.save()
    print("✅ Ticket order set in session")
    
    # Step 4: Test the create order endpoint
    response = client.post(
        '/create-cashfree-order/',
        data=json.dumps({'terms_accepted': True}),
        content_type='application/json'
    )
    
    print(f"\n=== Response Details ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response)}")
    
    if response.status_code == 200:
        try:
            response_data = json.loads(response.content)
            print(f"✅ Order creation successful!")
            print(f"Response: {response_data}")
            return True
        except json.JSONDecodeError:
            print(f"Response content: {response.content.decode()}")
    else:
        print(f"❌ Order creation failed")
        print(f"Response content: {response.content.decode()}")
        
        # Check if it's an authentication error
        if response.status_code == 401:
            print("🔍 This is the 401 error you're seeing!")
            
    return False

def test_direct_api_call():
    """Test the API directly using requests"""
    
    print("\n=== Testing Direct API Call ===")
    
    # Start a session to get CSRF token
    session = requests.Session()
    
    # Get CSRF token
    csrf_response = session.get('http://127.0.0.1:8000/')
    if csrf_response.status_code == 200:
        print("✅ Got initial page for CSRF token")
        
        # Try to extract CSRF token from response
        if 'csrftoken' in session.cookies:
            csrf_token = session.cookies['csrftoken']
            print(f"✅ CSRF token obtained: {csrf_token[:10]}...")
            
            # Make the API call with CSRF token
            headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token,
                'Referer': 'http://127.0.0.1:8000/'
            }
            
            response = session.post(
                'http://127.0.0.1:8000/create-cashfree-order/',
                data=json.dumps({'terms_accepted': True}),
                headers=headers
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
            if response.status_code == 401:
                print("🔍 Found the 401 error!")
            elif response.status_code == 302:
                print("🔍 Redirected - likely need to login first")
            
        else:
            print("❌ No CSRF token found")
    else:
        print("❌ Failed to get initial page")

if __name__ == "__main__":
    print("🔍 Testing to reproduce the 401 error...\n")
    
    # Test using Django test client (simulates logged-in user)
    flow_success = test_full_booking_flow()
    
    # Test using direct API call (simulates browser request)
    test_direct_api_call()
    
    print("\n=== Analysis ===")
    if flow_success:
        print("✅ The Django app can create orders when properly authenticated")
        print("💡 The 401 error might be due to:")
        print("   - Missing login session in your browser")
        print("   - Missing ticket order data in session")
        print("   - Browser cache showing old error")
    else:
        print("❌ There's still an issue with order creation")
        print("💡 Check the server logs for more details")
    
    print("\n📝 Troubleshooting steps:")
    print("1. Clear your browser cache and cookies")
    print("2. Make sure you're logged in to the Django app")
    print("3. Ensure you have ticket order data in your session")
    print("4. Check the browser's Network tab for the actual API call")
