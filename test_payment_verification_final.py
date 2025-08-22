#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from django.conf import settings
from cashfree_pg.api_client import Cashfree as CashfreeOriginal

def test_payment_verification_fixed():
    """Test the fixed payment verification approach."""
    
    # Test order ID from the logs
    test_order_id = "order_2542a8ad069d"
    api_version = "2023-08-01"
    
    print(f"Testing fixed payment verification for: {test_order_id}")
    
    try:
        # Validate credentials first
        if not settings.CASHFREE_CLIENT_ID or not settings.CASHFREE_CLIENT_SECRET:
            print("ERROR: Missing Cashfree credentials")
            return
            
        print(f"CLIENT_ID: {settings.CASHFREE_CLIENT_ID}")
        print(f"CLIENT_SECRET exists: {bool(settings.CASHFREE_CLIENT_SECRET)}")
        print(f"DEBUG mode: {settings.DEBUG}")
        
        # Initialize client with explicit string conversion
        cashfree_client = CashfreeOriginal()
        cashfree_client.XClientId = str(settings.CASHFREE_CLIENT_ID)
        cashfree_client.XClientSecret = str(settings.CASHFREE_CLIENT_SECRET)
        
        if settings.DEBUG:
            cashfree_client.XEnvironment = cashfree_client.SANDBOX
            print("Using SANDBOX environment")
        else:
            cashfree_client.XEnvironment = cashfree_client.PRODUCTION
            print("Using PRODUCTION environment")
        
        # Verify the client properties are set correctly
        print(f"Client XClientId: {repr(cashfree_client.XClientId)}")
        print(f"Client XClientSecret exists: {bool(cashfree_client.XClientSecret)}")
        print(f"Client XEnvironment: {cashfree_client.XEnvironment}")
        
        print("Calling PGFetchOrder with string parameters...")
        order_details = cashfree_client.PGFetchOrder(
            x_api_version=str(api_version),
            order_id=str(test_order_id)
        )
        
        print("SUCCESS: Order details fetched successfully!")
        print(f"Order details type: {type(order_details)}")
        
        if hasattr(order_details, 'data'):
            data = order_details.data
            print(f"Order status: {getattr(data, 'order_status', 'N/A')}")
            print(f"Payment status: {getattr(data, 'payment_status', 'N/A')}")
            print(f"Transaction ID: {getattr(data, 'transaction_id', 'N/A')}")
            print(f"Payment method: {getattr(data, 'payment_method', 'N/A')}")
            print(f"Order amount: {getattr(data, 'order_amount', 'N/A')}")
        else:
            print(f"Raw order details: {order_details}")
            
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_payment_verification_fixed()
