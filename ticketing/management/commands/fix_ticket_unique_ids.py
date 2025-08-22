from django.core.management.base import BaseCommand
from ticketing.utils_fix_tickets import fix_missing_ticket_unique_ids

class Command(BaseCommand):
    help = 'Fix tickets that are missing unique_id'

    def handle(self, *args, **options):
        self.stdout.write('Checking for tickets with missing unique_id...')
        
        fixed_count, total_count = fix_missing_ticket_unique_ids()
        
        if fixed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully fixed {fixed_count} out of {total_count} tickets with missing unique_id'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('No tickets needed fixing - all tickets have unique_id')
            )
