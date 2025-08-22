#!/usr/bin/env python
"""
Verify production mode setup and configuration.
⚠️ WARNING: This will verify PRODUCTION settings for REAL MONEY transactions!
"""

import os
import sys
import django
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')

# Setup Django
django.setup()

from django.conf import settings

def check_production_credentials():
    """Check that production credentials are properly set."""
    print("=== PRODUCTION CREDENTIALS CHECK ===")
    print("⚠️ WARNING: Checking PRODUCTION settings for REAL MONEY transactions!")
    
    client_id = os.getenv('CASHFREE_CLIENT_ID', '')
    environment = os.getenv('CASHFREE_ENVIRONMENT', '')
    
    # Check if still using placeholder credentials
    if 'YOUR_PRODUCTION' in client_id or 'placeholder' in client_id.lower():
        print("❌ STILL USING PLACEHOLDER CREDENTIALS!")
        print("   You must replace with actual production credentials from Cashfree dashboard")
        return False
    
    # Check environment
    if environment.upper() != 'PRODUCTION':
        print(f"❌ Environment is set to: {environment}")
        print("   Must be set to PRODUCTION")
        return False
    
    print("✅ Environment: PRODUCTION")
    print(f"✅ Client ID configured: {client_id[:8]}...")
    
    return True

def check_cashfree_api_setup():
    """Verify Cashfree API is configured for production."""
    print("\n=== CASHFREE API CONFIGURATION ===")
    
    try:
        from ticketing.cashfree_config import CashfreeSafe
        
        env_setting = getattr(settings, 'CASHFREE_ENVIRONMENT', 'Not set')
        print(f"Django setting CASHFREE_ENVIRONMENT: {env_setting}")
        
        if env_setting.upper() == 'PRODUCTION':
            print("✅ Django configured for PRODUCTION")
        else:
            print(f"❌ Django setting is {env_setting}, should be PRODUCTION")
            return False
        
        print("✅ CashfreeSafe class available")
        print("✅ Production API endpoints will be used")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking Cashfree setup: {e}")
        return False

def production_safety_warnings():
    """Display important production safety warnings."""
    print("\n" + "="*60)
    print("🚨 PRODUCTION MODE SAFETY WARNINGS 🚨")
    print("="*60)
    print()
    print("⚠️ REAL MONEY TRANSACTIONS:")
    print("   - All payments will charge actual money")
    print("   - Test with small amounts initially")
    print("   - Monitor transactions in Cashfree dashboard")
    print()
    print("⚠️ BEFORE GOING LIVE:")
    print("   - Replace placeholder credentials with real production credentials")
    print("   - Test thoroughly with small amounts")
    print("   - Verify webhook endpoints are working")
    print("   - Configure webhooks in Cashfree production dashboard")
    print()

def main():
    """Run all production verification checks."""
    print("💰 PRODUCTION MODE VERIFICATION 💰")
    print("⚠️ WARNING: This configures REAL MONEY transactions!")
    print()
    
    checks = [
        ("Production Credentials", check_production_credentials),
        ("Cashfree API Setup", check_cashfree_api_setup)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\n--- {name} ---")
        if check_func():
            passed += 1
        else:
            print(f"❌ {name} check failed")
    
    production_safety_warnings()
    
    print(f"\n=== PRODUCTION VERIFICATION SUMMARY ===")
    print(f"Passed: {passed}/{total} checks")
    
    if passed == total:
        print("🎉 Production configuration verified!")
        print("\n📋 NEXT STEPS:")
        print("1. Replace placeholder credentials with real production credentials")
        print("2. Update Vercel environment variables")
        print("3. Configure webhooks in Cashfree dashboard")
        print("4. Test with small amounts first")
        print("5. Deploy and monitor closely")
    else:
        print("⚠️ Some checks failed. Please resolve issues before deploying to production.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
