#!/usr/bin/env python
"""
Script to fix existing ticket data for consolidation
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from ticketing.models import Ticket
from django.db import transaction

def fix_existing_tickets():
    print("Fixing existing ticket data for consolidation...")
    
    with transaction.atomic():
        # Get all tickets that need fixing
        tickets_to_fix = Ticket.objects.filter(
            total_admission_count=1,  # Default value that needs fixing
            ticket_type__isnull=False  # Must have a ticket type
        )
        
        print(f"Found {tickets_to_fix.count()} tickets to fix")
        
        updated_count = 0
        for ticket in tickets_to_fix:
            # Calculate the correct total admission count
            correct_total = ticket.booking_quantity * ticket.ticket_type.attendees_per_ticket
            
            if ticket.total_admission_count != correct_total:
                old_value = ticket.total_admission_count
                ticket.total_admission_count = correct_total
                ticket.save(update_fields=['total_admission_count'])
                
                print(f"Updated ticket {ticket.ticket_number}: {old_value} -> {correct_total}")
                updated_count += 1
        
        print(f"\nSuccessfully updated {updated_count} tickets")

if __name__ == "__main__":
    fix_existing_tickets()
    print("✅ Ticket data fix complete!")
