#!/usr/bin/env python
import requests
import time

def test_payment_status_endpoint():
    """Test the payment status endpoint with the fixed verification."""
    
    url = "http://127.0.0.1:8000/payment-status/"
    params = {
        'order_id': 'order_2542a8ad069d',
        'session_order_id': 'order_2542a8ad069d',
        'payment_status': 'SUCCESS',
        'transaction_id': 'test_transaction_123'
    }
    
    print(f"Testing payment status endpoint...")
    print(f"URL: {url}")
    print(f"Parameters: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response content length: {len(response.content)}")
        
        # Check if it's HTML or JSON
        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            print(f"JSON Response: {response.json()}")
        elif 'text/html' in content_type:
            print("HTML Response received (likely a rendered page)")
            # Look for success indicators in HTML
            if 'success' in response.text.lower():
                print("✓ Payment success page detected")
            elif 'error' in response.text.lower():
                print("✗ Error page detected")
        else:
            print(f"Response text: {response.text[:500]}...")
            
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_payment_status_endpoint()
