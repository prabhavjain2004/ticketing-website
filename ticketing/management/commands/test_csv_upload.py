from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ticketing.utils import handle_event_csv_upload
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Test CSV upload functionality for event creation'

    def handle(self, *args, **options):
        # Get or create a test admin user
        admin_user, created = User.objects.get_or_create(
            email='admin@test.com',
            defaults={
                'first_name': 'Test',
                'last_name': 'Admin',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
                'email_verified': True
            }
        )
        
        if created:
            admin_user.set_password('testpass123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created test admin user: {admin_user.email}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing admin user: {admin_user.email}'))

        # Create a test CSV file
        csv_content = """title,description,event_type,short_description,date,time,end_date,end_time,venue,venue_address,venue_map_link,capacity,registration_deadline,venue_terms,event_terms,restrictions,status,featured,ticket_type_1,ticket_price_1,ticket_quantity_1,ticket_description_1,ticket_attendees_per_ticket_1,ticket_type_2,ticket_price_2,ticket_quantity_2,ticket_description_2,ticket_attendees_per_ticket_2,ticket_type_3,ticket_price_3,ticket_quantity_3,ticket_description_3,ticket_attendees_per_ticket_3,ticket_type_4,ticket_price_4,ticket_quantity_4,ticket_description_4,ticket_attendees_per_ticket_4
Test CSV Event 2025,This is a test event created via CSV upload to verify the functionality is working properly.,Conference,Test event for CSV upload verification,2025-12-15,14:00,2025-12-15,18:00,Test Venue,123 Test Street Test City,https://maps.google.com/?q=test,100,2025-12-10 23:59,No outside food allowed,All sales final,18+,DRAFT,False,General Admission,25.00,50,Standard entry ticket,1,VIP Pass,75.00,25,Premium seating and refreshments,1,Student Pass,15.00,25,Discounted student rate,1"""

        # Create a mock file object
        from django.core.files.base import ContentFile
        csv_file = ContentFile(csv_content.encode('utf-8'), name='test_event.csv')

        # Test the CSV upload function
        try:
            success, message, event_id = handle_event_csv_upload(csv_file, admin_user)
            
            if success:
                self.stdout.write(self.style.SUCCESS(f'✅ CSV upload successful!'))
                self.stdout.write(self.style.SUCCESS(f'Message: {message}'))
                self.stdout.write(self.style.SUCCESS(f'Event ID: {event_id}'))
                
                # Get the created event
                from ticketing.models import Event
                event = Event.objects.get(id=event_id)
                self.stdout.write(f'Event Title: {event.title}')
                self.stdout.write(f'Event Venue: {event.venue}')
                self.stdout.write(f'Event Capacity: {event.capacity}')
                self.stdout.write(f'Ticket Types: {event.ticket_types.count()}')
                
                for ticket_type in event.ticket_types.all():
                    self.stdout.write(f'  - {ticket_type.type_name}: ${ticket_type.price} x {ticket_type.quantity}')
                
            else:
                self.stdout.write(self.style.ERROR(f'❌ CSV upload failed!'))
                self.stdout.write(self.style.ERROR(f'Error: {message}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Exception occurred: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
