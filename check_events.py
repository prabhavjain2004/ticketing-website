#!/usr/bin/env python
"""
Check existing events in the database
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from ticketing.models import Event, Ticket

def check_events():
    """Check existing events and tickets"""
    
    print("Existing Events:")
    print("=" * 50)
    
    events = Event.objects.all()[:10]  # Get first 10 events
    
    for event in events:
        print(f"ID: {event.id}")
        print(f"Title: '{event.title}'")
        print(f"Event Type: '{event.event_type}'")
        print(f"Date: {event.date}")
        
        # Check if this event has tickets
        ticket_count = Ticket.objects.filter(event=event).count()
        print(f"Tickets: {ticket_count}")
        print("-" * 30)
    
    print(f"\nTotal events in database: {Event.objects.count()}")
    print(f"Total tickets in database: {Ticket.objects.count()}")

if __name__ == "__main__":
    check_events()
