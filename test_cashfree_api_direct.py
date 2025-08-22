#!/usr/bin/env python3
"""
Test script to directly test Cashfree API connectivity and order creation
without going through Django views.
"""

import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

# Import views to trigger Cashfree configuration
import ticketing.views

from ticketing.cashfree_config import CashfreeSafe as Cashfree

def test_cashfree_api_connection():
    """Test if we can connect to Cashfree API with current credentials"""
    
    print("=== Testing Cashfree API Connection ===")
    print(f"Environment: {settings.CASHFREE_ENVIRONMENT}")
    print(f"Client ID: {settings.CASHFREE_CLIENT_ID[:10]}...")
    print(f"Client Secret: {'*' * 20}{settings.CASHFREE_CLIENT_SECRET[-4:] if len(settings.CASHFREE_CLIENT_SECRET) > 4 else '****'}")
    
    try:
        # Initialize Cashfree client
        cashfree = Cashfree()
        print(f"Cashfree client initialized successfully")
        
        # Test by trying to create an order (the main functionality we need)
        print("\nTesting API connectivity by creating a test order...")
        return test_create_order()
        
    except Exception as e:
        print(f"❌ Failed to initialize Cashfree client: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False

def test_create_order():
    """Test creating a Cashfree order"""
    
    print("\n=== Testing Order Creation ===")
    
    try:
        from ticketing.cashfree_config import CashfreeSafe as Cashfree
        from cashfree_pg.models.create_order_request import CreateOrderRequest
        from cashfree_pg.models.customer_details import CustomerDetails
        from cashfree_pg.models.order_meta import OrderMeta
        
        # Initialize Cashfree client
        cashfree = Cashfree()
        
        # Create customer details first
        customer_details = CustomerDetails(
            customer_id="test_customer_123",
            customer_email="test@example.com",
            customer_phone="9876543210"
        )
        
        # Order meta
        order_meta = OrderMeta(
            return_url="https://example.com/return",
            notify_url="https://example.com/webhook"
        )
        
        # Create test order request with all required fields
        import time
        unique_order_id = f"test_order_{int(time.time())}"
        
        order_request = CreateOrderRequest(
            order_id=unique_order_id,
            order_amount=100.0,
            order_currency="INR",
            customer_details=customer_details,
            order_meta=order_meta
        )
        
        print(f"Creating test order: {order_request.order_id}")
        print(f"Amount: ₹{order_request.order_amount}")
        print(f"Customer: {order_request.customer_details.customer_email}")
        
        # Create the order
        response = cashfree.PGCreateOrder(
            x_api_version="2023-08-01",
            create_order_request=order_request
        )
        
        print("✅ Order created successfully!")
        print(f"Response type: {type(response)}")
        print(f"Response: {response}")
        
        # Try to access response data safely
        if hasattr(response, 'data'):
            response_data = response.data
            print(f"Order ID: {getattr(response_data, 'order_id', 'N/A')}")
            print(f"Order Status: {getattr(response_data, 'order_status', 'N/A')}")
            print(f"Payment Session ID: {getattr(response_data, 'payment_session_id', 'N/A')}")
        elif hasattr(response, 'order_id'):
            print(f"Order ID: {response.order_id}")
            print(f"Order Status: {response.order_status}")
            print(f"Payment Session ID: {response.payment_session_id}")
        else:
            print("Response structure not as expected, but order creation succeeded!")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create order: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        
        # If it's an API error, print more details
        if hasattr(e, 'body'):
            print(f"Error body: {e.body}")
        if hasattr(e, 'status'):
            print(f"HTTP Status: {e.status}")
        if hasattr(e, 'reason'):
            print(f"Reason: {e.reason}")
            
        return False

if __name__ == "__main__":
    print("🔍 Testing Cashfree API with new credentials...\n")
    
    # Test order creation (which tests both connectivity and credentials)
    success = test_cashfree_api_connection()
    
    print("\n=== SUMMARY ===")
    if success:
        print("✅ All tests passed! Cashfree integration is working correctly.")
        print("✅ You should now be able to create orders through your Django app.")
    else:
        print("❌ Tests failed.")
        print("💡 Check your Cashfree credentials and environment settings.")
    
    print(f"\n📝 Current Configuration:")
    print(f"Environment: {settings.CASHFREE_ENVIRONMENT}")
    print(f"Client ID: {settings.CASHFREE_CLIENT_ID}")
    print(f"Client Secret: {'*' * 40}{settings.CASHFREE_CLIENT_SECRET[-4:] if len(settings.CASHFREE_CLIENT_SECRET) > 4 else '****'}")
