#!/usr/bin/env python3
"""
Simple test to verify Cashfree credentials are properly loaded in Django.
"""

import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

# Import views to trigger Cashfree configuration
import ticketing.views

def check_environment():
    """Check environment variables and Django settings"""
    
    print("=== Environment Variables ===")
    print(f"CASHFREE_CLIENT_ID (env): {os.getenv('CASHFREE_CLIENT_ID', 'NOT SET')}")
    print(f"CASHFREE_CLIENT_SECRET (env): {os.getenv('CASHFREE_CLIENT_SECRET', 'NOT SET')}")
    print(f"CASHFREE_ENVIRONMENT (env): {os.getenv('CASHFREE_ENVIRONMENT', 'NOT SET')}")
    
    print("\n=== Django Settings ===")
    print(f"CASHFREE_CLIENT_ID: {getattr(settings, 'CASHFREE_CLIENT_ID', 'NOT SET')}")
    print(f"CASHFREE_CLIENT_SECRET: {getattr(settings, 'CASHFREE_CLIENT_SECRET', 'NOT SET')}")
    print(f"CASHFREE_ENVIRONMENT: {getattr(settings, 'CASHFREE_ENVIRONMENT', 'NOT SET')}")
    
    print("\n=== Cashfree Global Configuration ===")
    try:
        from ticketing.cashfree_config import CashfreeSafe as Cashfree
        cashfree = Cashfree()
        print(f"Cashfree.XClientId: {getattr(Cashfree, 'XClientId', 'NOT SET')}")
        print(f"Cashfree.XClientSecret: {getattr(Cashfree, 'XClientSecret', 'NOT SET')}")
        print(f"Cashfree.XEnvironment: {getattr(Cashfree, 'XEnvironment', 'NOT SET')}")
    except Exception as e:
        print(f"Error accessing Cashfree global config: {e}")

if __name__ == "__main__":
    check_environment()
