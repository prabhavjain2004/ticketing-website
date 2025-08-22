#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from django.conf import settings
from cashfree_pg.api_client import Cashfree as CashfreeOriginal
from cashfree_pg.models.cf_environment import CFEnvironment

def test_fetch_order_with_config():
    """Test fetching an order using PGConfig method."""
    
    # Test order ID from the logs
    test_order_id = "order_2542a8ad069d"
    api_version = "2023-08-01"
    
    print(f"Testing order fetch with PGConfig for: {test_order_id}")
    
    try:
        # Use PGConfig method instead of setting properties directly
        environment = CFEnvironment.SANDBOX if settings.DEBUG else CFEnvironment.PRODUCTION
        
        print(f"Using environment: {environment}")
        print(f"CLIENT_ID: {settings.CASHFREE_CLIENT_ID}")
        print(f"CLIENT_SECRET: {settings.CASHFREE_CLIENT_SECRET[:20]}...")
        
        # Configure using PGConfig method
        CashfreeOriginal.PGConfig(
            CFEnvironment=environment,
            XClientId=settings.CASHFREE_CLIENT_ID,
            XClientSecret=settings.CASHFREE_CLIENT_SECRET
        )
        
        print("PGConfig called successfully")
        
        # Create client instance
        cashfree_client = CashfreeOriginal()
        
        print("Calling PGFetchOrder...")
        order_details = cashfree_client.PGFetchOrder(
            x_api_version=api_version,
            order_id=test_order_id
        )
        
        print("SUCCESS: Order details fetched successfully!")
        print(f"Order details type: {type(order_details)}")
        
        if hasattr(order_details, 'data'):
            data = order_details.data
            print(f"Order status: {getattr(data, 'order_status', 'N/A')}")
            print(f"Payment status: {getattr(data, 'payment_status', 'N/A')}")
            print(f"Transaction ID: {getattr(data, 'transaction_id', 'N/A')}")
            print(f"Payment method: {getattr(data, 'payment_method', 'N/A')}")
        else:
            print(f"Raw order details: {order_details}")
            
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fetch_order_with_config()
