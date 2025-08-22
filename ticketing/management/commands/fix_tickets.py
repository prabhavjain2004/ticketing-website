from django.core.management.base import BaseCommand
from ticketing.utils_fix_tickets import fix_missing_ticket_unique_ids

class Command(BaseCommand):
    help = 'Fix tickets with missing unique_id field after successful payment'

    def handle(self, *args, **options):
        self.stdout.write("Fixing tickets with missing unique_id...")
        fixed_count, total_count = fix_missing_ticket_unique_ids()
        
        if fixed_count > 0:
            self.stdout.write(self.style.SUCCESS(f"Successfully fixed {fixed_count} tickets out of {total_count} with missing unique_id"))
        else:
            if total_count == 0:
                self.stdout.write(self.style.SUCCESS("No tickets with missing unique_id found. Everything looks good!"))
            else:
                self.stdout.write(self.style.WARNING(f"Found {total_count} tickets with issues, but couldn't fix any. Please check logs."))
