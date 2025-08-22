#!/usr/bin/env python3
"""
Fix for the webhook 401 UNAUTHORIZED issue.

Note: Cashfree does not provide a separate webhook secret key. 
Webhook signature verification uses the API Secret (Client Secret) from the API keys section.
"""

import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

def check_webhook_config():
    """Check current webhook configuration"""
    print("=== Current Webhook Configuration ===")
    print(f"CASHFREE_CLIENT_SECRET configured: {bool(settings.CASHFREE_CLIENT_SECRET)}")
    print(f"CASHFREE_CLIENT_SECRET value: {'*' * min(10, len(settings.CASHFREE_CLIENT_SECRET or '')) if settings.CASHFREE_CLIENT_SECRET else 'None'}")
    
    if not settings.CASHFREE_CLIENT_SECRET:
        print("❌ CASHFREE_CLIENT_SECRET is not set!")
        print("This is why the webhook is returning 401 UNAUTHORIZED")
        return False
    else:
        print("✅ CASHFREE_CLIENT_SECRET appears to be configured")
        print("✅ This will be used for webhook signature verification")
        return True

def fix_instructions():
    """Provide instructions to fix the issue"""
    print("\n=== HOW TO FIX THE WEBHOOK ISSUE ===")
    print("1. Log in to your Cashfree dashboard (production mode)")
    print("2. Go to Developers > API Keys")
    print("3. Copy your Client Secret (API Secret)")
    print("4. Update your .env file:")
    print("   CASHFREE_CLIENT_SECRET=your_actual_client_secret_from_step_3")
    print("5. Restart your server")
    print("\n✅ IMPORTANT: Cashfree uses the API Secret for webhook verification!")
    print("   - There is NO separate webhook secret key in Cashfree")
    print("   - The API Secret (Client Secret) is used for both API calls and webhook verification")
    print("   - The signature is calculated using HMAC SHA-256 of (timestamp + payload) with the API Secret")

def test_webhook_verification():
    """Test if webhook verification would work with current config"""
    from ticketing.views import verify_cashfree_signature
    
    # Test with dummy data
    test_payload = '{"test": "data"}'
    test_timestamp = "1234567890"
    test_signature = "dummy_signature"
    
    print("\n=== Testing Webhook Verification ===")
    try:
        result = verify_cashfree_signature(test_payload, test_signature, test_timestamp)
        print(f"Webhook verification test result: {result}")
        print("(This should be False unless you have the correct signature)")
    except Exception as e:
        print(f"Error during webhook verification: {e}")

if __name__ == "__main__":
    print("🔍 Diagnosing webhook authentication issue...\n")
    
    is_configured = check_webhook_config()
    
    if not is_configured:
        fix_instructions()
    
    test_webhook_verification()
    
    print("\n=== SUMMARY ===")
    if not is_configured:
        print("❌ Webhook will fail with 401 UNAUTHORIZED until Client Secret is configured")
        print("💡 This is why payments show as failed on your side but succeed on Cashfree's side")
    else:
        print("✅ Webhook configuration looks correct")
        print("💡 If you're still seeing issues, check your Cashfree dashboard webhook logs")
        print("💡 Remember: Cashfree uses the API Secret for webhook verification - no separate webhook secret!")
