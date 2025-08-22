import csv
import json
import logging
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from django.core.paginator import Paginator

from .models import Invoice, Event
from .invoice_utils import generate_invoice_pdf

logger = logging.getLogger(__name__)

def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'

@login_required
@user_passes_test(is_admin)
def admin_invoice_dashboard(request):
    """Admin dashboard for managing invoices"""
    # Get filter parameters
    event_id = request.GET.get('event_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Base query
    invoices_query = Invoice.objects.select_related('event', 'user', 'ticket', 'transaction').order_by('-created_at')
    
    # Apply filters if provided
    if event_id:
        invoices_query = invoices_query.filter(event_id=event_id)
    
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            invoices_query = invoices_query.filter(created_at__gte=start_date_obj)
        except ValueError:
            messages.error(request, "Invalid start date format")
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            # Add 1 day to include the end date fully
            end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
            invoices_query = invoices_query.filter(created_at__lte=end_date_obj)
        except ValueError:
            messages.error(request, "Invalid end date format")
    
    # Paginate results
    paginator = Paginator(invoices_query, 25)  # Show 25 invoices per page
    page_number = request.GET.get('page', 1)
    invoices = paginator.get_page(page_number)
    
    # Calculate totals for the filtered set (not just the current page)
    totals = invoices_query.aggregate(
        total_commission=Sum('commission'),
        total_sales=Sum('total_price'),
        count=Count('id')
    )
    
    # Get all events for the filter dropdown
    events = Event.objects.all().order_by('title')
    
    context = {
        'invoices': invoices,
        'events': events,
        'selected_event_id': int(event_id) if event_id and event_id.isdigit() else None,
        'start_date': start_date,
        'end_date': end_date,
        'total_commission': totals['total_commission'] or 0,
        'total_sales': totals['total_sales'] or 0,
        'total_count': totals['count'] or 0,
    }
    
    return render(request, 'ticketing/admin/invoice_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_download_invoice_csv(request):
    """Download all invoice data as CSV"""
    # Get filter parameters (same as in the dashboard view)
    event_id = request.GET.get('event_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Base query
    invoices_query = Invoice.objects.select_related('event', 'user', 'ticket', 'transaction').order_by('-created_at')
    
    # Apply filters if provided
    if event_id:
        invoices_query = invoices_query.filter(event_id=event_id)
    
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            invoices_query = invoices_query.filter(created_at__gte=start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
            invoices_query = invoices_query.filter(created_at__lte=end_date_obj)
        except ValueError:
            pass
    
    # Create HTTP response with CSV content
    response = HttpResponse(content_type='text/csv')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="tapnex_invoices_{timestamp}.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # --- 1. This is the corrected header row ---
    writer.writerow([
        'Invoice Number', 'Full Name', 'Mobile Number', 'Event Name', 'Ticket ID', 'Customer Email',
        'Base Price (₹)', 'TapNex Service Fee (₹)', 'Total Paid (₹)',
        'Purchase Date & Time', 'Transaction ID'
    ])
    
    # Add invoice data
    for invoice in invoices_query:
        # Get the full name from the user associated with the invoice
        full_name = f"{invoice.user.first_name} {invoice.user.last_name}"

        # --- 2. This is the corrected data row ---
        writer.writerow([
            invoice.invoice_number,
            full_name,
            invoice.user.mobile_number, # <-- Adds the mobile number
            invoice.event.title,
            invoice.ticket.ticket_number,
            invoice.user.email,
            invoice.base_price,
            invoice.commission,
            invoice.total_price,
            invoice.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            invoice.transaction.transaction_id
        ])
    
    return response

@login_required
@user_passes_test(is_admin)
def admin_download_invoice_pdf(request, invoice_id):
    """Generate and download a specific invoice as PDF"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    pdf_content = generate_invoice_pdf(invoice)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice-{invoice.invoice_number}.pdf"'
    response.write(pdf_content)
    
    return response

@login_required
@user_passes_test(is_admin)
def admin_view_invoice(request, invoice_id):
    """View details of a specific invoice"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    context = {
        'invoice': invoice,
    }
    
    return render(request, 'ticketing/admin/invoice_detail.html', context)
