#!/usr/bin/env python
"""
Test script to verify promo code analytics data structure and calculations
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.utils import timezone
from django.db.models import Sum, Count, Q
from ticketing.models import PromoCode, PromoCodeUsage, Event

def test_promo_analytics():
    """Test the promo code analytics calculations"""
    print("=== Promo Code Analytics Test ===")
    
    # Get total counts
    total_promos = PromoCode.objects.count()
    total_usage = PromoCodeUsage.objects.count()
    print(f"Total Promo Codes: {total_promos}")
    print(f"Total PromoCodeUsage records: {total_usage}")
    
    if total_usage == 0:
        print("No PromoCodeUsage records found - analytics will be empty")
        return
    
    # Test aggregate calculations
    active_promos = PromoCode.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).count()
    
    # Calculate totals from PromoCodeUsage
    usage_totals = PromoCodeUsage.objects.aggregate(
        total_discount=Sum('discount_amount'),
        total_revenue=Sum('order_total'),
        total_count=Count('id')
    )
    
    total_saved = usage_totals['total_discount'] or 0
    total_revenue = usage_totals['total_revenue'] or 0
    total_usage_count = usage_totals['total_count'] or 0
    
    # Calculate average redemption rate
    avg_redemption_rate = 0
    if total_promos > 0:
        redemption_rates = []
        for promo in PromoCode.objects.all():
            if promo.max_uses > 0:
                rate = (promo.current_uses / promo.max_uses) * 100
                redemption_rates.append(rate)
        
        if redemption_rates:
            avg_redemption_rate = sum(redemption_rates) / len(redemption_rates)
    
    print("\n=== Analytics Results ===")
    print(f"Active Promo Codes: {active_promos}")
    print(f"Total Amount Saved: ₹{total_saved:.2f}")
    print(f"Total Revenue Generated: ₹{total_revenue:.2f}")
    print(f"Average Redemption Rate: {avg_redemption_rate:.1f}%")
    print(f"Total Usage Records: {total_usage_count}")
    
    # Show sample PromoCodeUsage records
    print("\n=== Sample PromoCodeUsage Records ===")
    sample_usage = PromoCodeUsage.objects.select_related('promo_code', 'user', 'ticket').all()[:5]
    
    for usage in sample_usage:
        print(f"Code: {usage.promo_code.code}, "
              f"User: {usage.user.email}, "
              f"Order Total: ₹{usage.order_total}, "
              f"Discount: ₹{usage.discount_amount}, "
              f"Date: {usage.used_at}")
    
    # Show individual promo code stats
    print("\n=== Individual Promo Code Stats ===")
    for promo in PromoCode.objects.all()[:5]:
        print(f"Code: {promo.code}")
        print(f"  Current Uses: {promo.current_uses}")
        print(f"  Max Uses: {promo.max_uses}")
        print(f"  Total Saved: ₹{promo.total_amount_saved():.2f}")
        print(f"  Revenue Generated: ₹{promo.total_revenue_generated():.2f}")
        print(f"  Redemption Rate: {promo.redemption_rate():.1f}%")
        print()

if __name__ == "__main__":
    test_promo_analytics()
