#!/usr/bin/env python
import os
import django
import requests
import time

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from django.conf import settings

def test_direct_api_call():
    """Test fetching order using direct HTTP request instead of SDK."""
    
    test_order_id = "order_2542a8ad069d"
    api_version = "2023-08-01"
    
    print(f"Testing direct API call for: {test_order_id}")
    
    try:
        # Use sandbox endpoint
        base_url = "https://sandbox.cashfree.com/pg"
        endpoint = f"{base_url}/orders/{test_order_id}"
        
        headers = {
            "Accept": "application/json",
            "x-api-version": api_version,
            "x-client-id": settings.CASHFREE_CLIENT_ID,
            "x-client-secret": settings.CASHFREE_CLIENT_SECRET
        }
        
        print(f"URL: {endpoint}")
        print(f"Headers: {dict((k, v if k != 'x-client-secret' else v[:20] + '...') for k, v in headers.items())}")
        
        response = requests.get(endpoint, headers=headers, timeout=30)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: Order details retrieved!")
            print(f"Order status: {data.get('order_status', 'N/A')}")
            print(f"Payment status: {data.get('payment_status', 'N/A')}")
            print(f"Transaction ID: {data.get('transaction_id', 'N/A')}")
            print(f"Order amount: {data.get('order_amount', 'N/A')}")
            return data
        else:
            print(f"ERROR: API returned {response.status_code}")
            return None
            
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_direct_api_call()
