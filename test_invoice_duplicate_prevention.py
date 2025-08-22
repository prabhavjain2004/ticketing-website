#!/usr/bin/env python
"""
Test script to verify that duplicate invoice prevention is working
"""

import os
import sys
import django

# Setup Django environment
if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
    django.setup()

from ticketing.models import Ticket, Invoice, PaymentTransaction
from ticketing.invoice_utils import create_invoice_for_ticket
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_duplicate_prevention():
    """
    Test that trying to create duplicate invoices is prevented
    """
    logger.info("Testing duplicate invoice prevention...")
    
    # Find a ticket with an existing invoice
    ticket_with_invoice = Ticket.objects.filter(invoice__isnull=False).first()
    
    if not ticket_with_invoice:
        logger.warning("No tickets with invoices found - creating a test scenario")
        # Find any ticket and its transaction
        ticket = Ticket.objects.first()
        if not ticket:
            logger.error("No tickets found in database")
            return
        
        transaction = ticket.purchase_transaction
        if not transaction:
            logger.error("No transaction found for ticket")
            return
            
        # Create first invoice
        logger.info(f"Creating first invoice for ticket {ticket.ticket_number}")
        invoice1 = create_invoice_for_ticket(ticket, transaction)
        
        if invoice1:
            logger.info(f"✅ First invoice created: {invoice1.invoice_number}")
        else:
            logger.error("❌ Failed to create first invoice")
            return
    else:
        ticket = ticket_with_invoice
        transaction = ticket.purchase_transaction
        invoice1 = ticket.invoice
        logger.info(f"Using existing ticket {ticket.ticket_number} with invoice {invoice1.invoice_number}")
    
    # Try to create a duplicate invoice
    logger.info(f"Attempting to create duplicate invoice for ticket {ticket.ticket_number}")
    invoice2 = create_invoice_for_ticket(ticket, transaction)
    
    if invoice2 and invoice2.id == invoice1.id:
        logger.info(f"✅ Duplicate prevention works! Returned existing invoice: {invoice2.invoice_number}")
        return True
    elif invoice2 and invoice2.id != invoice1.id:
        logger.error(f"❌ Duplicate prevention failed! Created new invoice: {invoice2.invoice_number}")
        # Clean up the duplicate
        invoice2.delete()
        return False
    else:
        logger.error("❌ Failed to create or return invoice")
        return False

def test_invoice_relationship():
    """
    Test that the OneToOne relationship is working correctly
    """
    logger.info("Testing OneToOne relationship...")
    
    # Find a ticket with an invoice
    ticket = Ticket.objects.filter(invoice__isnull=False).first()
    
    if ticket:
        try:
            # Access the invoice through the reverse relationship
            invoice = ticket.invoice
            logger.info(f"✅ OneToOne relationship working: ticket.invoice = {invoice.invoice_number}")
            
            # Check that the invoice points back to the ticket
            if invoice.ticket.id == ticket.id:
                logger.info(f"✅ Reverse relationship working: invoice.ticket = {invoice.ticket.ticket_number}")
                return True
            else:
                logger.error("❌ Reverse relationship broken")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error accessing invoice relationship: {e}")
            return False
    else:
        logger.warning("No tickets with invoices found for relationship test")
        return True

if __name__ == "__main__":
    print("=== TapNex Invoice System Test ===")
    print("Testing duplicate prevention and relationships...")
    print()
    
    success1 = test_duplicate_prevention()
    success2 = test_invoice_relationship()
    
    if success1 and success2:
        print("\n✅ All tests passed! Invoice duplicate prevention is working correctly.")
    else:
        print("\n❌ Some tests failed. Please review the issues above.")
