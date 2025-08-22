#!/usr/bin/env python
"""
Script to backfill missing promo code usage records from existing successful transactions
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from ticketing.models import PaymentTransaction, PromoCode, PromoCodeUsage, Event
from django.utils import timezone

def backfill_promo_usage():
    """Backfill missing promo code usage records from successful transactions"""
    print("=== Backfilling Promo Code Usage Records ===")
    
    # Find successful transactions that have promo codes but no usage records
    successful_transactions = PaymentTransaction.objects.filter(
        status='SUCCESS'
    ).exclude(response_data__isnull=True)
    
    backfilled_count = 0
    error_count = 0
    
    for transaction in successful_transactions:
        try:
            # Extract ticket order data
            response_data = transaction.response_data or {}
            ticket_order = response_data.get('ticket_order', {})
            promo_code_str = ticket_order.get('promo_code')
            discount = ticket_order.get('discount', 0)
            subtotal = ticket_order.get('subtotal', 0)
            event_id = ticket_order.get('event_id')
            
            if not promo_code_str or discount <= 0:
                continue  # Skip transactions without promo codes
                
            print(f"Processing transaction {transaction.order_id} with promo {promo_code_str}")
            
            # Check if usage record already exists
            existing_usage = PromoCodeUsage.objects.filter(
                promo_code__code=promo_code_str,
                user=transaction.user,
                ticket__purchase_transaction=transaction
            ).first()
            
            if existing_usage:
                print(f"  Usage already exists, skipping")
                continue
                
            # Find the promo code and event
            try:
                event = Event.objects.get(id=event_id)
                promo_code = PromoCode.objects.get(code=promo_code_str, event=event)
            except (Event.DoesNotExist, PromoCode.DoesNotExist) as e:
                print(f"  Error: {e}")
                error_count += 1
                continue
                
            # Find the ticket associated with this transaction
            tickets = transaction.tickets.all()
            ticket = tickets.first() if tickets.exists() else None
            
            # Create the usage record
            PromoCodeUsage.objects.create(
                promo_code=promo_code,
                user=transaction.user,
                ticket=ticket,
                order_total=subtotal,
                discount_amount=discount
            )
            
            print(f"  ✓ Created usage record for {promo_code_str} (discount: ₹{discount})")
            backfilled_count += 1
            
        except Exception as e:
            print(f"  Error processing transaction {transaction.order_id}: {e}")
            error_count += 1
    
    print(f"\n=== Summary ===")
    print(f"Records backfilled: {backfilled_count}")
    print(f"Errors encountered: {error_count}")
    print(f"Total usage records now: {PromoCodeUsage.objects.count()}")

if __name__ == "__main__":
    backfill_promo_usage()
