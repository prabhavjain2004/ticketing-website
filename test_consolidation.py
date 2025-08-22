#!/usr/bin/env python
"""
Test script to verify ticket consolidation functionality
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from ticketing.models import Ticket, TicketType, Event, User

def test_consolidation():
    print("Testing ticket consolidation functionality...")
    
    # Get existing tickets to test with
    tickets = Ticket.objects.filter(total_admission_count__isnull=False)[:5]
    
    if not tickets:
        print("No consolidated tickets found. Testing may require running with existing data.")
        return
    
    print(f"\nFound {len(tickets)} consolidated tickets to test:")
    
    for ticket in tickets:
        print(f"\n--- Ticket {ticket.ticket_number} ---")
        print(f"Event: {ticket.event.title}")
        print(f"Ticket Type: {ticket.ticket_type.type_name if ticket.ticket_type else 'N/A'}")
        print(f"Booking Quantity: {ticket.booking_quantity}")
        print(f"Attendees per ticket: {ticket.ticket_type.attendees_per_ticket if ticket.ticket_type else 'N/A'}")
        print(f"Total Admission Count: {ticket.total_admission_count}")
        print(f"Status: {ticket.status}")
        
        # Verify the calculation
        if ticket.ticket_type:
            expected_total = ticket.booking_quantity * ticket.ticket_type.attendees_per_ticket
            if ticket.total_admission_count == expected_total:
                print("✅ Calculation correct!")
            else:
                print(f"❌ Calculation mismatch! Expected: {expected_total}, Got: {ticket.total_admission_count}")
        else:
            print("⚠️  No ticket type found")

def test_template_context():
    print("\n\nTesting template context functionality...")
    
    # Test a sample ticket
    sample_ticket = Ticket.objects.filter(total_admission_count__isnull=False).first()
    
    if sample_ticket:
        print(f"\n--- Testing with Ticket {sample_ticket.ticket_number} ---")
        
        # Simulate the context from event_pass view
        context_data = {
            'admit_count': sample_ticket.total_admission_count,
            'booking_quantity': sample_ticket.booking_quantity,
            'ticket_type_name': sample_ticket.ticket_type.type_name if sample_ticket.ticket_type else 'General',
            'attendees_per_ticket': sample_ticket.ticket_type.attendees_per_ticket if sample_ticket.ticket_type else 1
        }
        
        print("Template context data:")
        for key, value in context_data.items():
            print(f"  {key}: {value}")
            
        print("\n✅ Template context ready for consolidated display")
    else:
        print("❌ No consolidated tickets found for testing")

if __name__ == "__main__":
    test_consolidation()
    test_template_context()
    print("\n🎉 Consolidation testing complete!")
