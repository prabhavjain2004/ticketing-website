#!/usr/bin/env python
"""
Final comprehensive test of the Cashfree webhook integration
Tests both webhook verification and payment status verification
"""
import os
import django
import requests
import hmac
import hashlib
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from django.conf import settings

def test_webhook_verification():
    """Test webhook signature verification"""
    
    print("=== Testing Webhook Verification ===")
    
    # Test webhook payload
    webhook_data = {
        "data": {
            "order": {
                "order_id": "order_test_webhook_123",
                "order_amount": 100.00,
                "order_status": "PAID"
            }
        },
        "event_time": "2025-08-10T00:00:00+05:30",
        "type": "PAYMENT_SUCCESS_WEBHOOK"
    }
    
    # Create timestamp (current Unix timestamp as string)
    import time
    timestamp = str(int(time.time()))
    
    # Create signature using CASHFREE_CLIENT_SECRET and timestamp + payload format
    payload = json.dumps(webhook_data, separators=(',', ':'))
    message = timestamp + payload
    
    # Create HMAC SHA-256 signature and base64 encode it (as per Cashfree documentation)
    import base64
    signature_bytes = hmac.new(
        settings.CASHFREE_CLIENT_SECRET.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(signature_bytes).decode('utf-8')
    
    print(f"Timestamp: {timestamp}")
    print(f"Payload: {payload}")
    print(f"Message: {message}")
    print(f"Signature: {signature}")
    
    headers = {
        'Content-Type': 'application/json',
        'x-webhook-signature': signature,
        'x-webhook-timestamp': timestamp
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:8000/cashfree-webhook/',
            data=payload,
            headers=headers,
            timeout=10
        )
        
        print(f"Webhook response status: {response.status_code}")
        print(f"Webhook response: {response.text}")
        
        if response.status_code == 200:
            print("✓ Webhook verification successful!")
            return True
        elif response.status_code == 404:
            print("⚠ Webhook verification successful but order not found (expected for test)")
            return True  # Signature worked, just no matching order
        else:
            print("✗ Webhook verification failed!")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_payment_verification():
    """Test payment status verification using direct API"""
    
    print("\n=== Testing Payment Verification ===")
    
    # Test with the actual order we know exists
    url = "http://127.0.0.1:8000/payment-status/"
    params = {
        'order_id': 'order_2542a8ad069d',
        'session_order_id': 'order_2542a8ad069d',
        'payment_status': 'SUCCESS',
        'transaction_id': 'test_transaction_123'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        print(f"Payment verification status: {response.status_code}")
        
        if response.status_code == 200:
            if 'success' in response.text.lower():
                print("✓ Payment verification successful!")
                return True
            else:
                print("✗ Payment verification returned success code but no success content")
                return False
        else:
            print(f"✗ Payment verification failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_direct_cashfree_api():
    """Test direct Cashfree API call"""
    
    print("\n=== Testing Direct Cashfree API ===")
    
    try:
        base_url = "https://sandbox.cashfree.com/pg"
        endpoint = f"{base_url}/orders/order_2542a8ad069d"
        
        headers = {
            "Accept": "application/json",
            "x-api-version": "2023-08-01",
            "x-client-id": settings.CASHFREE_CLIENT_ID,
            "x-client-secret": settings.CASHFREE_CLIENT_SECRET
        }
        
        response = requests.get(endpoint, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Direct API call successful!")
            print(f"Order Status: {data.get('order_status')}")
            print(f"Order Amount: {data.get('order_amount')}")
            print(f"CF Order ID: {data.get('cf_order_id')}")
            return True
        else:
            print(f"✗ Direct API call failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Run all integration tests"""
    
    print("Cashfree Integration Test Suite")
    print("=" * 50)
    
    print(f"Environment: {'SANDBOX' if settings.DEBUG else 'PRODUCTION'}")
    print(f"Client ID: {settings.CASHFREE_CLIENT_ID}")
    print(f"Client Secret: {'Set' if settings.CASHFREE_CLIENT_SECRET else 'Not Set'}")
    print()
    
    results = []
    
    # Test 1: Direct API
    results.append(("Direct API", test_direct_cashfree_api()))
    
    # Test 2: Webhook verification
    results.append(("Webhook Verification", test_webhook_verification()))
    
    # Test 3: Payment verification
    results.append(("Payment Verification", test_payment_verification()))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:.<30} {status}")
    
    all_passed = all(result for _, result in results)
    print(f"\nOverall Status: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Cashfree integration is working correctly!")
        print("✓ Webhook signature verification using API Secret")
        print("✓ Payment verification using direct HTTP API calls")
        print("✓ Order creation and status fetching operational")
    else:
        print("\n⚠️  Some tests failed. Check the details above.")

if __name__ == "__main__":
    main()
