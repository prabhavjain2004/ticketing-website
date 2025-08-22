#!/usr/bin/env python
"""
Test our title parsing with the actual event data
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
from ticketing.templatetags.ticketing_extras import split_title_main, split_title_subtitle, has_dash_separator

def test_with_real_data():
    """Test with actual event data"""
    
    print("Testing with real event data:")
    print("=" * 50)
    
    # Get the WILDCARD event
    try:
        event = Event.objects.get(id=5)  # WILDCARD event
        print(f"Event ID: {event.id}")
        print(f"Original Title: '{event.title}'")
        print(f"Event Type: '{event.event_type}'")
        print()
        
        print("Current template behavior (BEFORE fix):")
        print(f"Main title: {event.title.upper()}")
        print(f"Subtitle: {event.event_type or 'The Beginning'}")
        print()
        
        print("New template behavior (AFTER fix):")
        if has_dash_separator(event.title):
            main_title = split_title_main(event.title)
            subtitle = split_title_subtitle(event.title)
            print(f"Main title: {main_title.upper()}")
            print(f"Subtitle: {subtitle.upper()}")
            print(f"Event type would be ignored since title has subtitle: {event.event_type}")
        else:
            print(f"Main title: {event.title.upper()}")
            if event.event_type:
                print(f"Subtitle: {event.event_type.upper()}")
        
        print()
        print("Tickets for this event:")
        tickets = Ticket.objects.filter(event=event)[:3]
        for ticket in tickets:
            print(f"- Ticket #{ticket.ticket_number} ({ticket.ticket_type.type_name})")
        
    except Event.DoesNotExist:
        print("Event not found")

if __name__ == "__main__":
    test_with_real_data()
