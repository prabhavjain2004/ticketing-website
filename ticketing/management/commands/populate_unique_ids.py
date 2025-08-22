import uuid
from django.core.management.base import BaseCommand
from django.db import transaction
from ticketing.models import Ticket


class Command(BaseCommand):
    help = 'Populate unique_id field for existing tickets that have None values'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find tickets with None unique_id
        tickets_without_unique_id = Ticket.objects.filter(unique_id__isnull=True)
        count = tickets_without_unique_id.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('All tickets already have unique_id values.')
            )
            return
        
        self.stdout.write(f'Found {count} tickets without unique_id')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would update {count} tickets')
            )
            for ticket in tickets_without_unique_id[:10]:  # Show first 10 as example
                self.stdout.write(f'  - Ticket ID {ticket.id} for event "{ticket.event.title}"')
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more tickets')
            return
        
        # Update tickets with unique UUIDs
        updated_count = 0
        with transaction.atomic():
            for ticket in tickets_without_unique_id:
                ticket.unique_id = uuid.uuid4()
                ticket.save(update_fields=['unique_id'])
                updated_count += 1
                
                if updated_count % 100 == 0:
                    self.stdout.write(f'Updated {updated_count} tickets...')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated unique_id for {updated_count} tickets'
            )
        )
