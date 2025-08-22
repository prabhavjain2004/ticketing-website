#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from django.conf import settings
from cashfree_pg.api_client import Cashfree as CashfreeOriginal

def test_fetch_order():
    """Test fetching an order using the same approach as the payment_status view."""
    
    # Test order ID from the logs
    test_order_id = "order_2542a8ad069d"
    api_version = "2023-08-01"
    
    print(f"Testing order fetch for: {test_order_id}")
    print(f"CASHFREE_CLIENT_ID: {repr(settings.CASHFREE_CLIENT_ID)}")
    print(f"CASHFREE_CLIENT_SECRET: {repr(settings.CASHFREE_CLIENT_SECRET[:20])}...")
    print(f"API Version: {api_version}")
    print(f"DEBUG mode: {settings.DEBUG}")
    
    try:
        # Setup client exactly as done in views.py
        cashfree_client = CashfreeOriginal()
        cashfree_client.XClientId = settings.CASHFREE_CLIENT_ID
        cashfree_client.XClientSecret = settings.CASHFREE_CLIENT_SECRET
        
        if settings.DEBUG:
            cashfree_client.XEnvironment = cashfree_client.SANDBOX
            print("Using SANDBOX environment")
        else:
            cashfree_client.XEnvironment = cashfree_client.PRODUCTION
            print("Using PRODUCTION environment")
        
        print("Calling PGFetchOrder...")
        print(f"Parameters: x_api_version='{api_version}', order_id='{test_order_id}'")
        
        # Check parameter types
        print(f"Type of api_version: {type(api_version)}")
        print(f"Type of order_id: {type(test_order_id)}")
        print(f"Type of CLIENT_ID: {type(settings.CASHFREE_CLIENT_ID)}")
        print(f"Type of CLIENT_SECRET: {type(settings.CASHFREE_CLIENT_SECRET)}")
        
        order_details = cashfree_client.PGFetchOrder(
            x_api_version=api_version,
            order_id=test_order_id
        )
        
        print("SUCCESS: Order details fetched successfully!")
        print(f"Order details type: {type(order_details)}")
        
        if hasattr(order_details, 'data'):
            data = order_details.data
            print(f"Order data: {data}")
            print(f"Order status: {getattr(data, 'order_status', 'N/A')}")
            print(f"Payment status: {getattr(data, 'payment_status', 'N/A')}")
            print(f"Transaction ID: {getattr(data, 'transaction_id', 'N/A')}")
        else:
            print(f"Raw order details: {order_details}")
            
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fetch_order()
