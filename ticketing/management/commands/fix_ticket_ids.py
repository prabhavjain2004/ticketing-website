import uuid
import string
import random
from django.core.management.base import BaseCommand
from django.db import transaction
from ticketing.models import Ticket


class Command(BaseCommand):
    help = 'Fix tickets with missing unique_id and unique_secure_token fields'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Find tickets with missing unique_id
        tickets_missing_unique_id = Ticket.objects.filter(
            unique_id__isnull=True,
            status__in=['SOLD', 'VALID']
        )
        
        # Find tickets with missing unique_secure_token
        tickets_missing_token = Ticket.objects.filter(
            unique_secure_token__isnull=True,
            status__in=['SOLD', 'VALID']
        )
        
        self.stdout.write(f'Found {tickets_missing_unique_id.count()} tickets missing unique_id')
        self.stdout.write(f'Found {tickets_missing_token.count()} tickets missing unique_secure_token')
        
        if not dry_run:
            fixed_count = 0
            
            with transaction.atomic():
                # Fix missing unique_id
                for ticket in tickets_missing_unique_id:
                    ticket.unique_id = uuid.uuid4()
                    ticket.save(update_fields=['unique_id'])
                    fixed_count += 1
                    self.stdout.write(f'Fixed unique_id for ticket {ticket.ticket_number}')
                
                # Fix missing unique_secure_token
                for ticket in tickets_missing_token:
                    if not ticket.unique_secure_token:
                        unique_token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))
                        ticket.unique_secure_token = unique_token
                        ticket.save(update_fields=['unique_secure_token'])
                        fixed_count += 1
                        self.stdout.write(f'Fixed unique_secure_token for ticket {ticket.ticket_number}')
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully fixed {fixed_count} tickets')
            )
        else:
            # Dry run - just show what would be fixed
            for ticket in tickets_missing_unique_id:
                self.stdout.write(f'Would fix unique_id for ticket {ticket.ticket_number} (ID: {ticket.id})')
            
            for ticket in tickets_missing_token:
                if not ticket.unique_secure_token:
                    self.stdout.write(f'Would fix unique_secure_token for ticket {ticket.ticket_number} (ID: {ticket.id})')
