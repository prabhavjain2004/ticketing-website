#!/usr/bin/env python3
"""
Test script to verify Cashfree environment configuration
"""
import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

def test_cashfree_environment():
    """Test Cashfree environment configuration"""
    print("=== Cashfree Environment Test ===")
    
    # Test import
    try:
        from ticketing.cashfree_config import get_cashfree_client, CashfreeSafe
        print("✓ Successfully imported Cashfree modules")
    except ImportError as e:
        print(f"✗ Failed to import Cashfree modules: {e}")
        return False
    
    # Test client creation for both environments
    try:
        # Test sandbox client
        sandbox_client = get_cashfree_client("sandbox")
        print(f"✓ Created sandbox client: {sandbox_client.XEnvironment}")
        
        # Test production client
        production_client = get_cashfree_client("production")
        print(f"✓ Created production client: {production_client.XEnvironment}")
        
        # Test automatic environment detection
        auto_client = get_cashfree_client()
        expected_env = "sandbox" if settings.DEBUG else "production"
        actual_env = "sandbox" if auto_client.XEnvironment == auto_client.SANDBOX else "production"
        print(f"✓ Auto-detected environment: {actual_env} (expected: {expected_env})")
        
        if actual_env == expected_env:
            print("✓ Environment auto-detection working correctly")
        else:
            print("✗ Environment auto-detection failed")
            return False
            
    except Exception as e:
        print(f"✗ Failed to create Cashfree clients: {e}")
        return False
    
    # Test singleton pattern
    try:
        client1 = get_cashfree_client("sandbox")
        client2 = get_cashfree_client("sandbox")
        
        if client1 is client2:
            print("✓ Singleton pattern working correctly")
        else:
            print("✗ Singleton pattern failed - different instances returned")
            return False
    except Exception as e:
        print(f"✗ Failed to test singleton pattern: {e}")
        return False
    
    print("\n=== Configuration Check ===")
    print(f"DEBUG Mode: {settings.DEBUG}")
    print(f"Client ID configured: {bool(getattr(settings, 'CASHFREE_CLIENT_ID', None))}")
    print(f"Client Secret configured: {bool(getattr(settings, 'CASHFREE_CLIENT_SECRET', None))}")
    print(f"Secret Key configured: {bool(getattr(settings, 'CASHFREE_SECRET_KEY', None))}")
    
    return True

if __name__ == "__main__":
    success = test_cashfree_environment()
    if success:
        print("\n🎉 All tests passed! Cashfree configuration is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the configuration.")
        exit(1)
