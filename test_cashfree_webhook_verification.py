#!/usr/bin/env python3
"""
Test script to verify Cashfree webhook signature verification implementation.
This script demonstrates the correct way to verify Cashfree webhook signatures
using the API Secret (Client Secret).
"""

import os
import django
import hmac
import hashlib
import base64
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

def test_cashfree_signature_verification():
    """Test the Cashfree webhook signature verification with a known example"""
    
    print("=== Testing Cashfree Webhook Signature Verification ===")
    print("Using API Secret (Client Secret) for verification as per Cashfree documentation\n")
    
    # Example payload and timestamp
    test_payload = '{"order_id":"test_order_123","order_status":"PAID","order_amount":100.00}'
    test_timestamp = "1640995200"  # Example timestamp
    
    # Check if we have the client secret configured
    if not settings.CASHFREE_CLIENT_SECRET:
        print("❌ CASHFREE_CLIENT_SECRET not configured!")
        print("Please set your Cashfree API Secret in the .env file")
        return False
    
    print(f"✅ Using Client Secret: {'*' * 20}{settings.CASHFREE_CLIENT_SECRET[-4:] if len(settings.CASHFREE_CLIENT_SECRET) > 4 else '****'}")
    print(f"Test payload: {test_payload}")
    print(f"Test timestamp: {test_timestamp}")
    
    # Generate the signature as Cashfree would
    message = test_timestamp + test_payload
    secret_bytes = settings.CASHFREE_CLIENT_SECRET.encode('utf-8')
    message_bytes = message.encode('utf-8')
    hash_obj = hmac.new(secret_bytes, msg=message_bytes, digestmod=hashlib.sha256)
    expected_signature = base64.b64encode(hash_obj.digest()).decode('utf-8')
    
    print(f"\nGenerated signature: {expected_signature}")
    
    # Now test our verification function
    from ticketing.views import verify_cashfree_signature
    
    print("\n=== Testing verification function ===")
    result = verify_cashfree_signature(test_payload, expected_signature, test_timestamp)
    
    if result:
        print("✅ Signature verification PASSED!")
        print("The webhook verification implementation is working correctly.")
    else:
        print("❌ Signature verification FAILED!")
        print("There may be an issue with the implementation.")
    
    # Test with wrong signature
    print("\n=== Testing with wrong signature ===")
    wrong_signature = "wrong_signature_here"
    result_wrong = verify_cashfree_signature(test_payload, wrong_signature, test_timestamp)
    
    if not result_wrong:
        print("✅ Correctly rejected wrong signature")
    else:
        print("❌ Incorrectly accepted wrong signature")
    
    return result and not result_wrong

def demonstrate_cashfree_webhook_format():
    """Demonstrate the exact format Cashfree uses for webhook signatures"""
    
    print("\n=== Cashfree Webhook Signature Format ===")
    print("1. Cashfree sends webhook with headers:")
    print("   - x-webhook-signature: <base64_encoded_signature>")
    print("   - x-webhook-timestamp: <unix_timestamp>")
    print("   - Content-Type: application/json")
    print("\n2. Signature calculation:")
    print("   - message = timestamp + raw_request_body")
    print("   - signature = base64(HMAC-SHA256(API_Secret, message))")
    print("\n3. Verification:")
    print("   - Extract timestamp and signature from headers")
    print("   - Calculate expected signature using same method")
    print("   - Compare using hmac.compare_digest() for security")
    
    print("\n=== Example Implementation ===")
    print("""
def verify_cashfree_signature(payload, signature, timestamp):
    secret_key = settings.CASHFREE_CLIENT_SECRET  # API Secret
    message = timestamp + payload
    expected_signature = base64.b64encode(
        hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
    ).decode('utf-8')
    return hmac.compare_digest(expected_signature, signature)
    """)

if __name__ == "__main__":
    print("🔍 Testing Cashfree webhook signature verification...\n")
    
    # Demonstrate the format
    demonstrate_cashfree_webhook_format()
    
    # Test the implementation
    success = test_cashfree_signature_verification()
    
    print("\n=== SUMMARY ===")
    if success:
        print("✅ Webhook signature verification is working correctly!")
        print("✅ Your integration should now properly verify Cashfree webhooks")
    else:
        print("❌ There are issues with the webhook verification")
        print("💡 Make sure CASHFREE_CLIENT_SECRET is properly configured")
    
    print("\n📝 Remember:")
    print("- Cashfree does NOT provide a separate webhook secret")
    print("- Use your API Secret (Client Secret) for webhook verification")
    print("- The signature format is: base64(HMAC-SHA256(API_Secret, timestamp + payload))")
