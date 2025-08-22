from django.core.management.base import BaseCommand
from django.db.models import Q
from ticketing.models import PromoCodeUsage, PaymentTransaction


class Command(BaseCommand):
    help = 'Clean up promo code usages for failed, cancelled, or sandbox payments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        self.stdout.write("Checking for invalid promo code usages...")

        # Find promo code usages associated with:
        # 1. Failed or cancelled transactions
        # 2. Sandbox transactions 
        # 3. Transactions with no payment transaction record (orphaned)
        
        invalid_usages = PromoCodeUsage.objects.filter(
            Q(ticket__purchase_transaction__status__in=['FAILED', 'CANCELLED', 'PENDING']) |
            Q(ticket__purchase_transaction__payment_gateway='SANDBOX') |
            Q(ticket__purchase_transaction__isnull=True)
        ).select_related('ticket__purchase_transaction', 'promo_code')

        total_count = invalid_usages.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS("No invalid promo code usages found. All usages are valid!")
            )
            return

        # Group by reason for reporting
        failed_count = invalid_usages.filter(
            ticket__purchase_transaction__status__in=['FAILED', 'CANCELLED', 'PENDING']
        ).count()
        
        sandbox_count = invalid_usages.filter(
            ticket__purchase_transaction__payment_gateway='SANDBOX'
        ).count()
        
        orphaned_count = invalid_usages.filter(
            ticket__purchase_transaction__isnull=True
        ).count()

        self.stdout.write(f"Found {total_count} invalid promo code usages:")
        self.stdout.write(f"  - {failed_count} for failed/cancelled/pending payments")
        self.stdout.write(f"  - {sandbox_count} for sandbox payments")
        self.stdout.write(f"  - {orphaned_count} orphaned (no transaction record)")

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING("DRY RUN: No changes will be made. Use --dry-run=False to actually clean up.")
            )
            
            # Show some examples
            for usage in invalid_usages[:5]:
                transaction_status = "No Transaction"
                if usage.ticket and usage.ticket.purchase_transaction:
                    transaction_status = f"{usage.ticket.purchase_transaction.status} ({usage.ticket.purchase_transaction.payment_gateway})"
                
                self.stdout.write(f"  - {usage.promo_code.code} by {usage.user.email} - {transaction_status}")
            
            if total_count > 5:
                self.stdout.write(f"  ... and {total_count - 5} more")
                
        else:
            # Actually delete the invalid usages
            self.stdout.write("Cleaning up invalid promo code usages...")
            
            # Also need to update promo code current_uses count
            promo_codes_to_update = set()
            for usage in invalid_usages:
                promo_codes_to_update.add(usage.promo_code)
            
            # Delete invalid usages
            deleted_count, _ = invalid_usages.delete()
            
            # Recalculate current_uses for affected promo codes based on valid usages only
            for promo_code in promo_codes_to_update:
                valid_usage_count = promo_code.promo_code_usages.filter(
                    ticket__purchase_transaction__status='SUCCESS'
                ).exclude(
                    ticket__purchase_transaction__payment_gateway='SANDBOX'
                ).count()
                
                old_count = promo_code.current_uses
                promo_code.current_uses = valid_usage_count
                promo_code.save()
                
                self.stdout.write(
                    f"Updated {promo_code.code}: current_uses {old_count} → {valid_usage_count}"
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully cleaned up {deleted_count} invalid promo code usages "
                    f"and updated {len(promo_codes_to_update)} promo codes."
                )
            )
