#!/usr/bin/env python
"""
Test script to verify ticket generation and display
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
sys.path.append('.')
django.setup()

from ticketing.models import PaymentTransaction, Ticket, User

def test_ticket_visibility():
    """Test that tickets are visible to users"""
    
    print("=== Testing Ticket Visibility ===")
    
    # Get a user with tickets
    users_with_tickets = User.objects.filter(tickets__isnull=False).distinct()
    
    if not users_with_tickets.exists():
        print("No users with tickets found!")
        return
        
    for user in users_with_tickets[:3]:  # Test first 3 users
        print(f"\nUser: {user.email}")
        
        # Get tickets the same way the my_tickets view does
        tickets = Ticket.objects.filter(
            customer=user,
            status__in=['SOLD', 'VALID']
        ).select_related('event', 'ticket_type')
        
        print(f"  Tickets found: {tickets.count()}")
        
        for ticket in tickets:
            print(f"    - {ticket.ticket_number}: {ticket.ticket_type.type_name}")
            print(f"      Event: {ticket.event.title}")
            print(f"      Status: {ticket.status}")
            print(f"      Unique ID: {ticket.unique_id}")
            print(f"      Booking Qty: {ticket.booking_quantity}")
            
            # Check if unique_id is set (required for online pass)
            if not ticket.unique_id:
                print("      ⚠️  Missing unique_id!")
            else:
                print("      ✅ Has unique_id")

def test_specific_user():
    """Test the specific user from the logs"""
    
    print("\n=== Testing Specific User (try.prabhav@gmail.com) ===")
    
    try:
        user = User.objects.get(email='try.prabhav@gmail.com')
        
        # Check tickets
        tickets = Ticket.objects.filter(
            customer=user,
            status__in=['SOLD', 'VALID']
        ).select_related('event', 'ticket_type')
        
        print(f"User: {user.email}")
        print(f"Total tickets: {tickets.count()}")
        
        if tickets.count() == 0:
            print("❌ No tickets found! User will see empty my-tickets page.")
        else:
            print("✅ Tickets found! User can view them in my-tickets page.")
            
            for ticket in tickets:
                print(f"  - {ticket.ticket_number} ({ticket.ticket_type.type_name})")
                print(f"    Order: {ticket.purchase_transaction.order_id if ticket.purchase_transaction else 'Unknown'}")
                
    except User.DoesNotExist:
        print("❌ User try.prabhav@gmail.com not found!")

if __name__ == '__main__':
    test_ticket_visibility()
    test_specific_user()
    print("\n=== Test Complete ===")
