#!/usr/bin/env python
"""
Cleanup script to remove duplicate invoices and ensure data integrity
Run this script to clean up existing duplicate invoices in the database
"""

import os
import sys
import django

# Setup Django environment
if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
    django.setup()

from django.db.models import Count
from ticketing.models import Invoice, Ticket
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_duplicate_invoices():
    """
    Remove duplicate invoices and keep only the earliest one for each ticket
    """
    logger.info("Starting duplicate invoice cleanup...")
    
    # Find tickets with multiple invoices using reverse foreign key lookup
    from django.db.models import Q
    
    # Get all invoices grouped by ticket
    duplicate_invoice_tickets = []
    
    # First, let's check if there are any existing duplicate invoices
    all_invoices = Invoice.objects.all().order_by('ticket_id', 'created_at')
    current_ticket_id = None
    current_ticket_invoices = []
    
    for invoice in all_invoices:
        if current_ticket_id != invoice.ticket_id:
            # New ticket, process previous ticket if it had duplicates
            if len(current_ticket_invoices) > 1:
                duplicate_invoice_tickets.append(current_ticket_invoices)
            
            # Start new ticket
            current_ticket_id = invoice.ticket_id
            current_ticket_invoices = [invoice]
        else:
            # Same ticket, add to list
            current_ticket_invoices.append(invoice)
    
    # Don't forget the last ticket
    if len(current_ticket_invoices) > 1:
        duplicate_invoice_tickets.append(current_ticket_invoices)
    
    total_tickets_affected = len(duplicate_invoice_tickets)
    total_duplicates_removed = 0
    
    logger.info(f"Found {total_tickets_affected} tickets with duplicate invoices")
    
    for ticket_invoices in duplicate_invoice_tickets:
        # Keep the first (earliest) invoice, delete the rest
        keep_invoice = ticket_invoices[0]
        invoices_to_delete = ticket_invoices[1:]
        
        logger.info(f"Ticket {keep_invoice.ticket.ticket_number}: keeping invoice {keep_invoice.invoice_number}, removing {len(invoices_to_delete)} duplicates")
        
        for invoice in invoices_to_delete:
            logger.info(f"  - Removing duplicate invoice {invoice.invoice_number}")
            invoice.delete()
            total_duplicates_removed += 1
    
    logger.info(f"Cleanup completed! Removed {total_duplicates_removed} duplicate invoices from {total_tickets_affected} tickets")

def verify_invoice_integrity():
    """
    Verify invoice data integrity after cleanup
    """
    logger.info("Verifying invoice data integrity...")
    
    # Check for invoices without tickets
    orphaned_invoices = Invoice.objects.filter(ticket__isnull=True).count()
    if orphaned_invoices > 0:
        logger.warning(f"Found {orphaned_invoices} orphaned invoices")
    
    # Check for tickets without invoices (this might be normal for some tickets)
    tickets_without_invoices = Ticket.objects.filter(invoice__isnull=True).count()
    logger.info(f"Found {tickets_without_invoices} tickets without invoices")
    
    # Check invoice number uniqueness
    total_invoices = Invoice.objects.count()
    unique_invoice_numbers = Invoice.objects.values('invoice_number').distinct().count()
    
    if total_invoices == unique_invoice_numbers:
        logger.info(f"✅ All {total_invoices} invoice numbers are unique")
    else:
        logger.error(f"❌ Invoice number duplication detected! {total_invoices} invoices but only {unique_invoice_numbers} unique numbers")
    
    # Verify cleanup worked
    # Check if there are any remaining tickets with multiple invoices
    duplicate_count = 0
    all_invoices = Invoice.objects.all().order_by('ticket_id')
    current_ticket_id = None
    
    for invoice in all_invoices:
        if current_ticket_id == invoice.ticket_id:
            duplicate_count += 1
            logger.warning(f"Duplicate found: Ticket {invoice.ticket.ticket_number} still has multiple invoices")
        current_ticket_id = invoice.ticket_id
    
    if duplicate_count == 0:
        logger.info("✅ No duplicate invoices found - cleanup successful!")
    else:
        logger.warning(f"⚠️  Still found {duplicate_count} potential duplicates")

if __name__ == "__main__":
    print("=== TapNex Invoice Cleanup Script ===")
    print("This script will remove duplicate invoices for tickets.")
    print("The earliest invoice for each ticket will be preserved.")
    print()
    
    response = input("Do you want to proceed with the cleanup? (y/N): ")
    
    if response.lower() in ['y', 'yes']:
        cleanup_duplicate_invoices()
        verify_invoice_integrity()
        print("\n✅ Cleanup completed successfully!")
    else:
        print("Cleanup cancelled.")
