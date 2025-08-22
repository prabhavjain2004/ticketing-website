#!/usr/bin/env python
"""
Test script to check the volunteer statistics feature
"""
import os
import sys
import django

# Add the project root to the path
sys.path.append('/Users/MOINAK/OneDrive/Desktop/TapNex/Tapnex/myproject')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from ticketing.models import User, Ticket, Event
from datetime import datetime, date

print("=== Volunteer Statistics Test ===")
print()

# Check volunteers
volunteers = User.objects.filter(role='VOLUNTEER')
print(f"Total volunteers: {volunteers.count()}")

for volunteer in volunteers:
    print(f"- {volunteer.email} ({volunteer.first_name} {volunteer.last_name})")

print()

# Check validated tickets
validated_tickets = Ticket.objects.filter(validated_by__isnull=False).select_related('validated_by', 'event')
print(f"Total validated tickets: {validated_tickets.count()}")

for ticket in validated_tickets[:5]:  # Show first 5
    validator = ticket.validated_by
    event_name = ticket.event.title if ticket.event else "Unknown Event"
    validated_time = ticket.used_at.strftime('%Y-%m-%d %H:%M') if ticket.used_at else "Unknown time"
    print(f"- Ticket {ticket.ticket_number} validated by {validator.email} for {event_name} at {validated_time}")

print()

# Check events
events = Event.objects.all()
print(f"Total events: {events.count()}")

for event in events[:3]:  # Show first 3
    print(f"- {event.title} ({event.date})")

print()
print("=== Test Complete ===")
print()
print("To access the volunteer statistics page:")
print("1. Login as an admin user")
print("2. Go to: http://127.0.0.1:8000/admin-panel/volunteer-statistics/")
print("3. Or use the 'Volunteer Statistics' link in the admin navigation")
