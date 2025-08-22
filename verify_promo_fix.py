#!/usr/bin/env python
"""
Promo Code Analytics Fix Verification Script

This script helps verify that the promo code analytics fix is working correctly.
It checks promo code usage data and ensures only successful, non-sandbox transactions are counted.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from ticketing.models import PromoCode, PromoCodeUsage, PaymentTransaction, Ticket
from django.db.models import Q


def check_promo_code_analytics():
    """Check current state of promo code analytics"""
    
    print("=" * 60)
    print("PROMO CODE ANALYTICS VERIFICATION")
    print("=" * 60)
    
    # Get all promo codes
    promo_codes = PromoCode.objects.all()
    print(f"\nTotal Promo Codes: {promo_codes.count()}")
    
    if not promo_codes.exists():
        print("No promo codes found in the system.")
        return
    
    print("\nChecking each promo code:")
    print("-" * 60)
    
    for promo_code in promo_codes:
        print(f"\nPromo Code: {promo_code.code} ({promo_code.event.title})")
        
        # Get all usages
        all_usages = promo_code.promo_code_usages.all()
        print(f"  Total PromoCodeUsage records: {all_usages.count()}")
        
        # Get successful usages only
        successful_usages = promo_code.promo_code_usages.filter(
            ticket__purchase_transaction__status='SUCCESS'
        ).exclude(
            ticket__purchase_transaction__payment_gateway='SANDBOX'
        )
        print(f"  Successful non-sandbox usages: {successful_usages.count()}")
        
        # Get invalid usages
        invalid_usages = promo_code.promo_code_usages.filter(
            Q(ticket__purchase_transaction__status__in=['FAILED', 'CANCELLED', 'PENDING']) |
            Q(ticket__purchase_transaction__payment_gateway='SANDBOX') |
            Q(ticket__purchase_transaction__isnull=True)
        )
        print(f"  Invalid usages (failed/sandbox/orphaned): {invalid_usages.count()}")
        
        # Check current analytics values
        print(f"  Current uses (stored): {promo_code.current_uses}")
        print(f"  Total tickets booked (method): {promo_code.total_tickets_booked()}")
        print(f"  Total amount saved: ₹{promo_code.total_amount_saved()}")
        print(f"  Total revenue generated: ₹{promo_code.total_revenue_generated()}")
        print(f"  Redemption rate: {promo_code.redemption_rate():.1f}%")
        
        # Check if current_uses matches successful transactions
        expected_uses = successful_usages.count()
        if promo_code.current_uses != expected_uses:
            print(f"  ⚠️  WARNING: current_uses ({promo_code.current_uses}) doesn't match successful usages ({expected_uses})")
        else:
            print(f"  ✅ current_uses matches successful transactions")
            
        # Show details of invalid usages if any
        if invalid_usages.exists():
            print(f"  📝 Invalid usage details:")
            for usage in invalid_usages:
                if usage.ticket and usage.ticket.purchase_transaction:
                    tx = usage.ticket.purchase_transaction
                    print(f"    - {usage.user.email}: {tx.status} ({tx.payment_gateway})")
                else:
                    print(f"    - {usage.user.email}: No transaction record")


def check_payment_transactions():
    """Check payment transaction statuses"""
    
    print("\n" + "=" * 60)
    print("PAYMENT TRANSACTIONS SUMMARY")
    print("=" * 60)
    
    # Count transactions by status
    statuses = ['SUCCESS', 'FAILED', 'CANCELLED', 'PENDING', 'CREATED']
    
    for status in statuses:
        count = PaymentTransaction.objects.filter(status=status).count()
        print(f"  {status}: {count}")
    
    # Count by gateway
    print(f"\nBy Payment Gateway:")
    gateways = PaymentTransaction.objects.values_list('payment_gateway', flat=True).distinct()
    for gateway in gateways:
        count = PaymentTransaction.objects.filter(payment_gateway=gateway).count()
        print(f"  {gateway}: {count}")


def suggest_cleanup():
    """Suggest cleanup actions"""
    
    print("\n" + "=" * 60)
    print("CLEANUP RECOMMENDATIONS")
    print("=" * 60)
    
    # Check for invalid promo usages
    invalid_usages = PromoCodeUsage.objects.filter(
        Q(ticket__purchase_transaction__status__in=['FAILED', 'CANCELLED', 'PENDING']) |
        Q(ticket__purchase_transaction__payment_gateway='SANDBOX') |
        Q(ticket__purchase_transaction__isnull=True)
    )
    
    if invalid_usages.exists():
        print(f"\n⚠️  Found {invalid_usages.count()} invalid promo code usages")
        print("   These should be cleaned up to ensure accurate analytics.")
        print("   Run: python manage.py cleanup_promo_usages --dry-run")
        print("   Then: python manage.py cleanup_promo_usages")
    else:
        print("\n✅ No invalid promo code usages found!")
    
    # Check for promo codes with mismatched current_uses
    mismatched_promos = []
    for promo_code in PromoCode.objects.all():
        expected_uses = promo_code.total_tickets_booked()
        if promo_code.current_uses != expected_uses:
            mismatched_promos.append((promo_code, promo_code.current_uses, expected_uses))
    
    if mismatched_promos:
        print(f"\n⚠️  Found {len(mismatched_promos)} promo codes with mismatched current_uses:")
        for promo, current, expected in mismatched_promos:
            print(f"   {promo.code}: stored={current}, should be={expected}")
        print("   These will be fixed when you run the cleanup command.")
    else:
        print("\n✅ All promo codes have accurate current_uses counts!")


if __name__ == "__main__":
    try:
        check_promo_code_analytics()
        check_payment_transactions() 
        suggest_cleanup()
        
        print("\n" + "=" * 60)
        print("VERIFICATION COMPLETE")
        print("=" * 60)
        print("\nThe fix ensures that promo code analytics only count:")
        print("  ✅ Successful payments (status = 'SUCCESS')")
        print("  ✅ Real money transactions (not 'SANDBOX')")
        print("  ✅ Tickets with valid transaction records")
        
    except Exception as e:
        print(f"Error running verification: {e}")
        sys.exit(1)
