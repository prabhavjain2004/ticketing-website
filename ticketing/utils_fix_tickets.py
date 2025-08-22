# Utility function to find and fix tickets missing unique_id

import uuid
from datetime import timedelta
from django.utils import timezone
from ticketing.models import Ticket, PaymentTransaction

def fix_missing_ticket_unique_ids():
    """
    Find tickets that have a successful payment transaction but are missing unique_id
    and fix them by generating a new UUID.
    
    Returns tuple of (fixed_count, total_count)
    """
    # Find successful payments from the last 30 days
    recent_success_transactions = PaymentTransaction.objects.filter(
        status='SUCCESS',
        created_at__gte=timezone.now() - timedelta(days=30)
    )
    
    # Find tickets linked to these transactions but missing unique_id
    broken_tickets = Ticket.objects.filter(
        purchase_transaction__in=recent_success_transactions,
        unique_id__isnull=True
    )
    
    fixed_count = 0
    for ticket in broken_tickets:
        ticket.unique_id = uuid.uuid4()
        if not ticket.unique_secure_token:
            ticket.unique_secure_token = str(uuid.uuid4())
        ticket.save()
        fixed_count += 1
        
    return fixed_count, len(broken_tickets)
