#!/usr/bin/env python
"""
Create sample data for testing volunteer statistics
"""
import os
import sys
import django
from datetime import datetime, timedelta
import uuid

# Add the project root to the path
sys.path.append('/Users/MOINAK/OneDrive/Desktop/TapNex/Tapnex/myproject')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from ticketing.models import User, Ticket, Event, TicketType
from django.utils import timezone

print("=== Creating Sample Data for Volunteer Statistics ===")
print()

# Get volunteers and events
volunteers = User.objects.filter(role='VOLUNTEER')
events = Event.objects.all()

if not volunteers.exists():
    print("No volunteers found. Please create volunteer users first.")
    exit(1)

if not events.exists():
    print("No events found. Please create events first.")
    exit(1)

event = events.first()
print(f"Using event: {event.title}")

# Create ticket types if they don't exist
ticket_type, created = TicketType.objects.get_or_create(
    event=event,
    type_name="General Admission",
    defaults={
        'price': 25.00,
        'quantity': 100,
        'description': 'General admission ticket',
        'attendees_per_ticket': 1
    }
)

print(f"Using ticket type: {ticket_type.type_name}")

# Create some sample tickets and validate them
sample_tickets_data = [
    {"number": "WILD001", "attendees": 1},
    {"number": "WILD002", "attendees": 2},
    {"number": "WILD003", "attendees": 1},
    {"number": "WILD004", "attendees": 3},
    {"number": "WILD005", "attendees": 1},
    {"number": "WILD006", "attendees": 2},
    {"number": "WILD007", "attendees": 1},
    {"number": "WILD008", "attendees": 1},
    {"number": "WILD009", "attendees": 4},
    {"number": "WILD010", "attendees": 1},
]

created_count = 0
validated_count = 0

for i, ticket_data in enumerate(sample_tickets_data):
    ticket_number = ticket_data["number"]
    attendees = ticket_data["attendees"]
    
    # Check if ticket already exists
    if Ticket.objects.filter(ticket_number=ticket_number).exists():
        print(f"Ticket {ticket_number} already exists, skipping...")
        continue
    
    # Create ticket
    ticket = Ticket.objects.create(
        event=event,
        ticket_type=ticket_type,
        ticket_number=ticket_number,
        status='USED',  # Set as used since it's validated
        unique_secure_token=str(uuid.uuid4()),
        total_admission_count=attendees,
        booking_quantity=1,
        purchase_date=timezone.now() - timedelta(days=7),  # Purchased a week ago
    )
    created_count += 1
    
    # Assign to a volunteer and validate
    volunteer = volunteers[i % len(volunteers)]  # Rotate through volunteers
    
    # Set validation details
    validation_time = timezone.now() - timedelta(
        hours=i*2,  # Spread validations over time
        minutes=i*15
    )
    
    ticket.validated_by = volunteer
    ticket.used_at = validation_time
    ticket.save()
    
    validated_count += 1
    
    print(f"Created and validated ticket {ticket_number} "
          f"for {attendees} attendee(s) by {volunteer.email} "
          f"at {validation_time.strftime('%Y-%m-%d %H:%M')}")

print()
print(f"=== Summary ===")
print(f"Created {created_count} new tickets")
print(f"Validated {validated_count} tickets")
print(f"Total volunteers with activity: {len(volunteers)}")
print()
print("You can now test the volunteer statistics page with this sample data!")
print("URL: http://127.0.0.1:8000/admin-panel/volunteer-statistics/")
