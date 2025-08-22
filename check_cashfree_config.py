#!/usr/bin/env python
"""
Checks current Cashfree configuration and prints details.
"""
import os
import sys
import django
import json

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from django.conf import settings
from cashfree_pg.api_client import Cashfree
# We'll set up proper SSL verification manually here
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("=== Cashfree Configuration Check ===\n")
print(f"Cashfree Environment: {getattr(settings, 'CASHFREE_ENVIRONMENT', 'Not set')}")
print(f"Client ID configured: {bool(settings.CASHFREE_CLIENT_ID)}")
print(f"Client Secret configured: {bool(settings.CASHFREE_CLIENT_SECRET)}")
print(f"API Environment: {'PRODUCTION' if Cashfree.XEnvironment == Cashfree.PRODUCTION else 'SANDBOX'}")
print("\nNote: Client Secret is used for both API calls and webhook verification")

# Try to make a simple API call to validate credentials
try:
    print("\nAttempting to connect to Cashfree API...")
    client = Cashfree()
    # Make sure SSL verification is enabled
    if hasattr(client.api_client, 'configuration'):
        client.api_client.configuration.verify_ssl = True
    
    response = client.PGFetchPGDetails(
        x_api_version="2023-08-01"
    )
    
    print("\n✅ Successfully connected to Cashfree API!")
    print(f"Payment Gateway Details:")
    print(f"  Merchant ID: {response.data.merchant_id}")
    print(f"  Merchant Name: {response.data.name}")
    print(f"  Status: {response.data.status}")
    print(f"  Activated On: {response.data.activated_on}")
    
except Exception as e:
    print(f"\n❌ Failed to connect to Cashfree API: {str(e)}")
    
print("\nNote: If you're getting authentication errors, make sure you've set the correct")
print("production credentials in your environment variables.")
