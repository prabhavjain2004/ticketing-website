#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from ticketing.cashfree_config import get_cashfree_client

def test_payment_verification_with_cashfree_safe():
    """Test payment verification using the CashfreeSafe client."""
    
    # Test order ID from the logs
    test_order_id = "order_2542a8ad069d"
    api_version = "2023-08-01"
    
    print(f"Testing payment verification with CashfreeSafe for: {test_order_id}")
    
    try:
        # Get configured client using the existing helper function
        cashfree_client = get_cashfree_client(env="sandbox")
        
        print(f"Client type: {type(cashfree_client)}")
        print(f"Client XClientId: {repr(cashfree_client.XClientId)}")
        print(f"Client XEnvironment: {cashfree_client.XEnvironment}")
        
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
            print(f"Order amount: {getattr(data, 'order_amount', 'N/A')}")
        else:
            print(f"Raw order details: {order_details}")
            
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_payment_verification_with_cashfree_safe()
