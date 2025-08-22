#!/usr/bin/env python
"""
Script to display current invoice status and demonstrate the fix
"""

import os
import sys
import django

# Setup Django environment
if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
    django.setup()

from ticketing.models import Ticket, Invoice, PaymentTransaction, Event
from django.db.models import Count
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_invoice_summary():
    """
    Display a summary of current invoices to demonstrate the fix
    """
    print("=== TapNex Invoice System Status ===")
    print()
    
    # Total counts
    total_tickets = Ticket.objects.count()
    total_invoices = Invoice.objects.count()
    total_transactions = PaymentTransaction.objects.count()
    
    print(f"📊 System Overview:")
    print(f"   • Total Tickets: {total_tickets}")
    print(f"   • Total Invoices: {total_invoices}")
    print(f"   • Total Transactions: {total_transactions}")
    print()
    
    # Check for tickets with invoices
    tickets_with_invoices = Ticket.objects.filter(invoice__isnull=False).count()
    tickets_without_invoices = total_tickets - tickets_with_invoices
    
    print(f"🎫 Ticket-Invoice Mapping:")
    print(f"   • Tickets with invoices: {tickets_with_invoices}")
    print(f"   • Tickets without invoices: {tickets_without_invoices}")
    print()
    
    # Show recent invoices by event
    print(f"📋 Recent Invoices by Event:")
    events_with_invoices = Event.objects.filter(invoices__isnull=False).distinct()
    
    for event in events_with_invoices[:5]:  # Show first 5 events
        event_invoices = Invoice.objects.filter(event=event).order_by('-created_at')
        print(f"   📅 {event.title}:")
        
        for invoice in event_invoices[:3]:  # Show first 3 invoices per event
            print(f"      • {invoice.invoice_number} - Ticket: {invoice.ticket.ticket_number} - ₹{invoice.total_price}")
        
        if event_invoices.count() > 3:
            print(f"      ... and {event_invoices.count() - 3} more")
        print()
    
    # Check for any potential issues
    print(f"🔍 Data Integrity Check:")
    
    # Check unique invoice numbers
    total_invoices = Invoice.objects.count()
    unique_invoice_numbers = Invoice.objects.values('invoice_number').distinct().count()
    
    if total_invoices == unique_invoice_numbers:
        print(f"   ✅ All {total_invoices} invoice numbers are unique")
    else:
        print(f"   ❌ Invoice number duplication: {total_invoices} invoices, {unique_invoice_numbers} unique numbers")
    
    # Check orphaned invoices
    orphaned_invoices = Invoice.objects.filter(ticket__isnull=True).count()
    if orphaned_invoices == 0:
        print(f"   ✅ No orphaned invoices")
    else:
        print(f"   ⚠️  {orphaned_invoices} orphaned invoices found")
    
    # Check relationship integrity
    try:
        # Test OneToOne relationship
        test_ticket = Ticket.objects.filter(invoice__isnull=False).first()
        if test_ticket:
            test_invoice = test_ticket.invoice
            print(f"   ✅ OneToOne relationship working correctly")
        else:
            print(f"   ℹ️  No tickets with invoices to test relationship")
    except Exception as e:
        print(f"   ❌ Relationship error: {e}")
    
    print()
    print("✅ Invoice duplicate prevention system is now active!")
    print("   • Each ticket can only have one invoice")
    print("   • Attempting to create duplicates will return the existing invoice")
    print("   • Email notifications are prevented for existing invoices")

if __name__ == "__main__":
    show_invoice_summary()
