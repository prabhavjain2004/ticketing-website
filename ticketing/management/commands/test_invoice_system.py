from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from ticketing.models import Event, TicketType, Ticket, PaymentTransaction, EventCommission, Invoice
from ticketing.invoice_utils import create_invoice_for_ticket, send_invoice_email
from django.db.models import Sum

User = get_user_model()

class Command(BaseCommand):
    help = 'Test the invoice system functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Create test data for invoice testing',
        )
        parser.add_argument(
            '--test-invoice-generation',
            action='store_true',
            help='Test invoice generation for existing tickets',
        )

    def handle(self, *args, **options):
        if options['create_test_data']:
            self.create_test_data()
        elif options['test_invoice_generation']:
            self.test_invoice_generation()
        else:
            self.stdout.write(
                self.style.WARNING('Please specify --create-test-data or --test-invoice-generation')
            )

    def create_test_data(self):
        """Create test data for invoice testing"""
        self.stdout.write('Creating test data...')

        # Create test user
        user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={
                'first_name': 'Test',
                'last_name': 'User',
                'role': 'CUSTOMER'
            }
        )
        if created:
            self.stdout.write(f'Created test user: {user.email}')

        # Create test event
        event, created = Event.objects.get_or_create(
            title='Test Event for Invoice System',
            defaults={
                'description': 'A test event to verify invoice functionality',
                'event_type': 'Test',
                'date': timezone.now().date() + timezone.timedelta(days=30),
                'time': timezone.now().time(),
                'venue': 'Test Venue',
                'capacity': 100,
                'organizer': user,
                'status': 'PUBLISHED'
            }
        )
        if created:
            self.stdout.write(f'Created test event: {event.title}')

        # Create commission settings
        commission, created = EventCommission.objects.get_or_create(
            event=event,
            defaults={
                'commission_type': 'percentage',
                'commission_value': Decimal('10.00'),  # 10% commission
                'created_by': user
            }
        )
        if created:
            self.stdout.write(f'Created commission settings: {commission.commission_type} {commission.commission_value}')

        # Create ticket type
        ticket_type, created = TicketType.objects.get_or_create(
            event=event,
            type_name='Test Ticket',
            defaults={
                'price': Decimal('500.00'),
                'quantity': 50,
                'description': 'Test ticket type'
            }
        )
        if created:
            self.stdout.write(f'Created ticket type: {ticket_type.type_name} - ₹{ticket_type.price}')

        # Create payment transaction
        transaction, created = PaymentTransaction.objects.get_or_create(
            order_id='test_order_001',
            defaults={
                'user': user,
                'transaction_id': 'test_txn_001',
                'amount': Decimal('500.00'),
                'status': 'SUCCESS'
            }
        )
        if created:
            self.stdout.write(f'Created payment transaction: {transaction.order_id}')

        # Create ticket
        ticket, created = Ticket.objects.get_or_create(
            ticket_number='TEST001',
            defaults={
                'event': event,
                'ticket_type': ticket_type,
                'customer': user,
                'status': 'SOLD',
                'purchase_date': timezone.now(),
                'unique_secure_token': 'test_token_001',
                'purchase_transaction': transaction
            }
        )
        if created:
            self.stdout.write(f'Created ticket: {ticket.ticket_number}')

        self.stdout.write(
            self.style.SUCCESS('Test data created successfully!')
        )

    def test_invoice_generation(self):
        """Test invoice generation for existing tickets"""
        self.stdout.write('Testing invoice generation...')

        # Find tickets without invoices
        tickets_without_invoices = Ticket.objects.filter(
            status='SOLD',
            invoices__isnull=True
        ).select_related('event', 'ticket_type', 'customer', 'purchase_transaction')

        if not tickets_without_invoices.exists():
            self.stdout.write(
                self.style.WARNING('No tickets found without invoices. Create test data first.')
            )
            return

        self.stdout.write(f'Found {tickets_without_invoices.count()} tickets without invoices')

        for ticket in tickets_without_invoices:
            try:
                # Create invoice
                invoice = create_invoice_for_ticket(ticket, ticket.purchase_transaction)
                
                if invoice:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Created invoice {invoice.invoice_number} for ticket {ticket.ticket_number}'
                        )
                    )
                    self.stdout.write(f'  - Base Price: ₹{invoice.base_price}')
                    self.stdout.write(f'  - Commission: ₹{invoice.commission}')
                    self.stdout.write(f'  - Total: ₹{invoice.total_price}')
                    
                    # Test email sending (optional)
                    try:
                        email_sent = send_invoice_email(invoice)
                        if email_sent:
                            self.stdout.write(f'  - Email sent successfully to {invoice.user.email}')
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'  - Failed to send email to {invoice.user.email}')
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'  - Email error: {str(e)}')
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to create invoice for ticket {ticket.ticket_number}')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error processing ticket {ticket.ticket_number}: {str(e)}')
                )

        # Show summary
        total_invoices = Invoice.objects.count()
        total_revenue = Invoice.objects.aggregate(
            total=Sum('commission')
        )['total'] or Decimal('0.00')
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('INVOICE SYSTEM SUMMARY')
        self.stdout.write('='*50)
        self.stdout.write(f'Total Invoices: {total_invoices}')
        self.stdout.write(f'Total Revenue: ₹{total_revenue}')
        self.stdout.write('='*50)
        
        self.stdout.write(
            self.style.SUCCESS('Invoice generation test completed!')
        )
