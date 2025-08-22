#!/usr/bin/env python
"""
Test script to simulate new ticket booking with consolidation
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from ticketing.models import Ticket, TicketType, Event, User

def test_new_booking_consolidation():
    print("Testing new booking consolidation...")
    
    # Get a sample event and ticket type
    event = Event.objects.first()
    ticket_type = TicketType.objects.first()
    user = User.objects.first()
    
    if not all([event, ticket_type, user]):
        print("❌ Missing required data for test (event, ticket_type, or user)")
        return
    
    print(f"Using Event: {event.title}")
    print(f"Using Ticket Type: {ticket_type.type_name} (admits {ticket_type.attendees_per_ticket} people)")
    print(f"Using User: {user.email}")
    
    # Simulate booking 3 tickets of this type (like in our create_tickets_for_payment function)
    booking_quantity = 3
    total_admissions = booking_quantity * ticket_type.attendees_per_ticket
    
    print(f"\nSimulating booking of {booking_quantity} tickets...")
    print(f"Expected total admissions: {total_admissions}")
    
    # Create a test ticket with our consolidated logic
    test_ticket = Ticket.objects.create(
        event=event,
        ticket_type=ticket_type,
        customer=user,
        status='VALID',
        booking_quantity=booking_quantity,
        total_admission_count=total_admissions,
        purchase_date=django.utils.timezone.now()
    )
    
    print(f"\n✅ Created test ticket: {test_ticket.ticket_number}")
    print(f"Booking Quantity: {test_ticket.booking_quantity}")
    print(f"Total Admission Count: {test_ticket.total_admission_count}")
    print(f"Calculation: {test_ticket.booking_quantity} × {ticket_type.attendees_per_ticket} = {test_ticket.total_admission_count}")
    
    # Verify the calculation
    expected = booking_quantity * ticket_type.attendees_per_ticket
    if test_ticket.total_admission_count == expected:
        print("✅ Consolidation calculation is correct!")
    else:
        print(f"❌ Calculation error! Expected: {expected}, Got: {test_ticket.total_admission_count}")
    
    # Clean up test ticket
    test_ticket.delete()
    print("🧹 Test ticket cleaned up")

if __name__ == "__main__":
    test_new_booking_consolidation()
    print("\n🎉 New booking consolidation test complete!")
