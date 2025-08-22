#!/usr/bin/env python
"""
Script to fix missing tickets for successful payment transactions
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
sys.path.append('.')
django.setup()

from ticketing.models import PaymentTransaction, Ticket, TicketType, Event
from django.contrib.auth import get_user_model
import uuid as uuid_module
from django.utils import timezone
from django.db import transaction
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_ticket_number():
    """Generate a unique ticket number"""
    import secrets
    import string
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

def fix_missing_tickets():
    """Fix missing tickets for successful payment transactions"""
    
    # Get all successful transactions that don't have tickets
    successful_transactions = PaymentTransaction.objects.filter(status='SUCCESS')
    
    for trans in successful_transactions:
        existing_tickets = Ticket.objects.filter(purchase_transaction=trans)
        
        if existing_tickets.exists():
            logger.info(f"Transaction {trans.order_id} already has {existing_tickets.count()} tickets")
            continue
            
        logger.info(f"Processing transaction {trans.order_id} - creating missing tickets")
        
        # Get ticket order data from transaction
        response_data = trans.response_data or {}
        ticket_order = response_data.get('ticket_order', {})
        if not ticket_order:
            logger.warning(f"No ticket_order data found for transaction {trans.order_id}")
            continue
            
        # Get event
        event_id = ticket_order.get('event_id')
        if not event_id:
            logger.warning(f"No event_id found for transaction {trans.order_id}")
            continue
            
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            logger.error(f"Event {event_id} does not exist for transaction {trans.order_id}")
            continue
            
        # Get selected tickets
        selected_tickets = ticket_order.get('ticket_types', [])
        if not selected_tickets:
            logger.warning(f"No ticket_types found for transaction {trans.order_id}")
            continue
            
        # Create tickets
        created_tickets = []
        with transaction.atomic():
            for ticket_data in selected_tickets:
                ticket_type_id = ticket_data.get('id')
                if not ticket_type_id:
                    logger.warning(f"No ticket type ID found in ticket data: {ticket_data}")
                    continue
                    
                try:
                    ticket_type = TicketType.objects.get(id=ticket_type_id)
                except TicketType.DoesNotExist:
                    logger.error(f"TicketType {ticket_type_id} does not exist")
                    continue
                
                # Calculate consolidated ticket details
                attendees_per_ticket = ticket_type.attendees_per_ticket or 1
                booking_quantity = ticket_data.get('quantity', 1)
                total_admissions = booking_quantity * attendees_per_ticket
                
                logger.info(f"Creating ticket for {ticket_type.type_name}: qty={booking_quantity}, total_admissions={total_admissions}")
                
                # Create single consolidated ticket
                ticket = Ticket.objects.create(
                    event=event,
                    ticket_type=ticket_type,
                    customer=trans.user,
                    ticket_number=generate_ticket_number(),
                    status='SOLD',
                    purchase_date=trans.created_at,
                    unique_secure_token=str(uuid_module.uuid4()),
                    unique_id=uuid_module.uuid4(),
                    purchase_transaction=trans,
                    booking_quantity=booking_quantity,
                    total_admission_count=total_admissions
                )
                created_tickets.append(ticket)
                logger.info(f"Created ticket {ticket.ticket_number}")
            
            # Update transaction response data
            if created_tickets:
                trans.response_data = {
                    **(trans.response_data or {}),
                    'tickets_created': [t.id for t in created_tickets],
                    'ticket_count': len(created_tickets),
                    'ticket_creation_timestamp': timezone.now().isoformat(),
                    'fixed_by_script': True
                }
                trans.save()
                
                logger.info(f"Successfully created {len(created_tickets)} tickets for transaction {trans.order_id}")
            else:
                logger.warning(f"No tickets created for transaction {trans.order_id}")

if __name__ == '__main__':
    print("=== Fixing Missing Tickets ===")
    fix_missing_tickets()
    print("=== Done ===")
