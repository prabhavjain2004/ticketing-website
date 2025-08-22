#!/usr/bin/env python
"""
Generate a test ticket to verify our template fix works
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from ticketing.models import Event, Ticket, TicketType
from django.urls import reverse

def get_test_ticket_info():
    """Get information about a test ticket for the WILDCARD event"""
    
    try:
        # Get the WILDCARD event
        event = Event.objects.get(id=5)
        print(f"Event: {event.title}")
        print(f"Event Type: {event.event_type}")
        
        # Get a ticket for this event
        ticket = Ticket.objects.filter(event=event).first()
        
        if ticket:
            print(f"Found ticket: {ticket.ticket_number}")
            print(f"Ticket type: {ticket.ticket_type.type_name}")
            
            # Construct the ticket URL
            print(f"\nYou can view this ticket at:")
            print(f"http://127.0.0.1:8000/ticket/{ticket.id}/")
            print(f"http://127.0.0.1:8000/ticket/view/{ticket.id}/")
            
            # Also print some debug info about the ticket model
            print(f"\nTicket ID: {ticket.id}")
            print(f"Status: {ticket.status}")
            
            return ticket
        else:
            print("No tickets found for this event")
            return None
            
    except Event.DoesNotExist:
        print("WILDCARD event not found")
        return None

if __name__ == "__main__":
    get_test_ticket_info()
