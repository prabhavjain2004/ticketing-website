#!/usr/bin/env python
"""
Verify production settings and Cashfree configuration.
Run this script before deploying to production to ensure all required settings are in place.
"""
import os
import sys
import django
from dotenv import load_dotenv

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from django.conf import settings
from cashfree_pg.api_client import Cashfree
# We'll set up proper SSL verification manually here
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_environment_variables():
    """Check for required environment variables."""
    required_vars = [
        'CASHFREE_CLIENT_ID',
        'CASHFREE_CLIENT_SECRET', 
        'CASHFREE_SECRET_KEY',
        'EMAIL_HOST_PASSWORD',
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def check_cashfree_configuration():
    """Check Cashfree configuration."""
    print(f"Current Cashfree environment: {getattr(settings, 'CASHFREE_ENVIRONMENT', 'Not set')}")
    
    # Check if we're in production mode when we should be
    if settings.DEBUG:
        print("⚠️ WARNING: DEBUG is set to True. Set DEBUG=False for production.")
    
    if getattr(settings, 'CASHFREE_ENVIRONMENT', '').upper() != 'PRODUCTION' and not settings.DEBUG:
        print("❌ CASHFREE_ENVIRONMENT is not set to PRODUCTION but DEBUG is False")
        return False
    
    # Check Cashfree API client configuration
    if Cashfree.XClientId and Cashfree.XClientSecret:
        print("✅ Cashfree API credentials are configured")
        if Cashfree.XEnvironment == Cashfree.PRODUCTION:
            print("✅ Cashfree is set to PRODUCTION mode")
        else:
            print("❌ Cashfree is NOT set to PRODUCTION mode")
            return False
    else:
        print("❌ Cashfree API credentials are not properly configured")
        return False
    
    return True

def check_security_settings():
    """Check security-related settings."""
    if not settings.DEBUG:  # Only check in production mode
        if not settings.SECURE_SSL_REDIRECT:
            print("❌ SECURE_SSL_REDIRECT is not enabled")
            return False
        
        if not settings.SESSION_COOKIE_SECURE:
            print("❌ SESSION_COOKIE_SECURE is not enabled")
            return False
            
        if not settings.CSRF_COOKIE_SECURE:
            print("❌ CSRF_COOKIE_SECURE is not enabled")
            return False
            
        print("✅ Security settings are properly configured")
        return True
    else:
        print("⚠️ Security settings not checked (DEBUG mode)")
        return True

def check_allowed_hosts():
    """Check that allowed hosts is properly configured for production."""
    if '*' in settings.ALLOWED_HOSTS:
        print("⚠️ WARNING: ALLOWED_HOSTS contains '*', which is not secure for production")
        return False
    
    if 'tickets.tapnex.tech' not in settings.ALLOWED_HOSTS:
        print("❌ Production domain 'tickets.tapnex.tech' is not in ALLOWED_HOSTS")
        return False
    
    print(f"✅ ALLOWED_HOSTS is properly configured: {settings.ALLOWED_HOSTS}")
    return True

def check_csrf_trusted_origins():
    """Check CSRF trusted origins settings."""
    if not hasattr(settings, 'CSRF_TRUSTED_ORIGINS') or not settings.CSRF_TRUSTED_ORIGINS:
        print("❌ CSRF_TRUSTED_ORIGINS is not configured")
        return False
        
    if 'https://tickets.tapnex.tech' not in settings.CSRF_TRUSTED_ORIGINS:
        print("❌ Production domain not in CSRF_TRUSTED_ORIGINS")
        return False
    
    print(f"✅ CSRF_TRUSTED_ORIGINS is properly configured")
    return True

if __name__ == "__main__":
    print("=== Production Settings Verification ===\n")
    
    all_checks_passed = (
        check_environment_variables() and
        check_cashfree_configuration() and
        check_security_settings() and
        check_allowed_hosts() and
        check_csrf_trusted_origins()
    )
    
    if all_checks_passed:
        print("\n✅ All production checks passed! Ready for deployment.")
        sys.exit(0)
    else:
        print("\n❌ Some checks failed. Please fix the issues before deploying to production.")
        sys.exit(1)
