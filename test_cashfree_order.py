#!/usr/bin/env python
import os
import django
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from cashfree_pg.models.create_order_request import CreateOrderRequest
from cashfree_pg.models.order_meta import OrderMeta
from cashfree_pg.models.customer_details import CustomerDetails
from ticketing.cashfree_config import CashfreeSafe as Cashfree

def test_cashfree_order():
    try:
        # Configure Cashfree client
        client_id = os.getenv('CASHFREE_CLIENT_ID')
        client_secret = os.getenv('CASHFREE_CLIENT_SECRET')
        
        print(f"Client ID: {client_id[:10]}..." if client_id else "None")
        print(f"Client Secret: {client_secret[:10]}..." if client_secret else "None")
        
        Cashfree.XClientId = client_id
        Cashfree.XClientSecret = client_secret
        Cashfree.XEnvironment = Cashfree.SANDBOX
        
        # Create a test order
        order_id = f"test_order_{uuid.uuid4().hex[:12]}"
        
        create_order_request = CreateOrderRequest(
            order_amount=100.0,
            order_currency="INR",
            customer_details=CustomerDetails(
                customer_id="test_customer_001",
                customer_name="Test Customer",
                customer_email="test@example.com",
                customer_phone="9999999999",
            ),
            order_meta=OrderMeta(
                return_url="https://test.com/return",
                notify_url="https://test.com/webhook"
            ),
            order_id=order_id
        )
        
        print(f"Creating test order: {order_id}")
        
        # Make API call
        api_response = Cashfree().PGCreateOrder(
            x_api_version="2023-08-01",
            create_order_request=create_order_request,
        )
        
        print("API Response:")
        print(f"Response data: {api_response.data}")
        
        if hasattr(api_response, 'data') and api_response.data:
            payment_session_id = getattr(api_response.data, 'payment_session_id', None)
            cf_order_id = getattr(api_response.data, 'order_id', None)
            payment_link = getattr(api_response.data, 'payment_link', None)
            
            print(f"Success!")
            print(f"Payment Session ID: {payment_session_id}")
            print(f"Order ID: {cf_order_id}")
            print(f"Payment Link: {payment_link}")
        else:
            print("Error: Invalid response structure")
            
    except Exception as e:
        print(f"Error creating Cashfree order: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cashfree_order()
