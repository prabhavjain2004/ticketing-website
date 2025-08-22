import secrets
import random
import logging
import json
import uuid as uuid_module
import string
import qrcode
import traceback as traceback_module
import time
import tempfile
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO, StringIO
import base64
import hmac
import hashlib
import os
import re  # Import the regular expression module
import csv
import datetime
from datetime import datetime as dt
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_GET
from .models import Event, TicketType, Ticket
from .forms import (
    CustomUserCreationForm, EventForm, ProfileUpdateForm,
    PromoCodeForm, EventStaffForm, OTPForm
)
from .models import User, Event, Ticket, PromoCode, EventStaff, TicketType, PromoCodeUsage, PaymentTransaction
from .utils import generate_otp, send_otp_email
# Removed: from weasyprint import HTML, CSS
# Removed: import imgkit

# cashfree
from cashfree_pg.models.create_order_request import CreateOrderRequest
from cashfree_pg.models.order_meta import OrderMeta
from cashfree_pg.models.customer_details import CustomerDetails
from ticketing.cashfree_config import CashfreeSafe as Cashfree
# Add these imports at the top of ticketing/views.py
import hmac
import hashlib
import base64
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
from .models import TicketPurchase 
from .utils import generate_tickets_for_purchase # Assuming you have a function like this



# --- CASHFREE CONFIGURATION (from settings) ---
from django.conf import settings
import logging

# Get the logger instance for this module
logger = logging.getLogger(__name__)

# Validate Cashfree configuration
if not settings.CASHFREE_CLIENT_ID:
    logger.critical("CRITICAL ERROR: CASHFREE_CLIENT_ID not configured. Payments will not work!")
if not settings.CASHFREE_CLIENT_SECRET:
    logger.critical("CRITICAL ERROR: CASHFREE_CLIENT_SECRET not configured. Payments and webhook verification will not work!")

logger.info(f"Cashfree Environment: {getattr(settings, 'CASHFREE_ENVIRONMENT', 'PRODUCTION')}")
logger.info(f"Client ID configured: {bool(settings.CASHFREE_CLIENT_ID)}")
logger.info(f"Client Secret configured: {bool(settings.CASHFREE_CLIENT_SECRET)}")

Cashfree.XClientId = settings.CASHFREE_CLIENT_ID
Cashfree.XClientSecret = settings.CASHFREE_CLIENT_SECRET

# Enforce PRODUCTION mode for deployment
if settings.DEBUG:
    Cashfree.XEnvironment = Cashfree.SANDBOX
    logger.warning("Using Cashfree SANDBOX environment (Debug mode)")
else:
    Cashfree.XEnvironment = Cashfree.PRODUCTION
    logger.info("Using Cashfree PRODUCTION environment")

CASHFREE_API_VERSION = "2023-08-01"

def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'

def is_organizer(user):
    return user.is_authenticated and user.role == 'ORGANIZER'

def is_volunteer(user):
    return user.is_authenticated and user.role == 'VOLUNTEER'

def is_customer(user):
    return user.is_authenticated and user.role == 'CUSTOMER'

from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
import os

def download_csv_guide(request):
    """
    Downloads the CSV upload guide as a text file
    """
    guide_path = os.path.join(settings.BASE_DIR, 'ticketing', 'static', 'core', 'docs', 'csv_upload_guide.md')

    if os.path.exists(guide_path):
        with open(guide_path, 'r') as file:
            content = file.read()

        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="Event_CSV_Instructions.txt"'
        return response

@login_required
@user_passes_test(is_customer)
def my_tickets(request):
    # Debug logging
    logger.info(f"my_tickets view called for user {request.user.email} (ID: {request.user.id})")
    
    # First check all tickets for this user
    all_user_tickets = Ticket.objects.filter(customer=request.user)
    logger.info(f"Total tickets for user {request.user.email}: {all_user_tickets.count()}")
    
    tickets = Ticket.objects.filter(
        customer=request.user,
        status__in=['SOLD', 'VALID']
    ).select_related('event', 'ticket_type')

    logger.info(f"Filtered tickets (SOLD/VALID) for user {request.user.email}: {tickets.count()}")
    
    # Log each ticket for debugging
    for ticket in tickets:
        logger.info(f"  - Ticket #{ticket.ticket_number}: {ticket.event.title}, Status: {ticket.status}")

    # Ensure all tickets have unique_id for instant pass generation
    tickets_fixed = 0
    for ticket in tickets:
        if not ticket.unique_id:
            ticket.unique_id = uuid_module.uuid4()
            if not ticket.unique_secure_token:
                ticket.unique_secure_token = str(uuid_module.uuid4())
            ticket.save()
            tickets_fixed += 1
    
    if tickets_fixed > 0:
        logger.info(f"Fixed {tickets_fixed} tickets with missing unique_id for user {request.user.id}")

    context = {
        'tickets': tickets
    }

    logger.info(f"Rendering my_tickets.html with {len(tickets)} tickets")
    return render(request, 'core/my_tickets.html', context)



# Verification function removed

def get_event_data():
    events = Event.objects.filter(status='PUBLISHED').order_by('-created_at').prefetch_related('ticket_types')
    events_with_prices = []
    for event in events:
        min_price = float('inf')
        for ticket_type in event.ticket_types.all():
            if ticket_type.price < min_price:
                min_price = ticket_type.price
        events_with_prices.append({
            'event': event,
            'min_price': min_price if min_price != float('inf') else None,
            'tickets_are_live': event.tickets_are_live
        })
    return events_with_prices

def home(request):
    events_with_prices = get_event_data()
    return render(request, 'core/home.html', {'events': events_with_prices})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            if not user.email_verified:
                request.session['user_pk_for_verification'] = user.pk
                otp = generate_otp()
                user.email_verification_otp = otp
                user.email_verification_otp_created_at = timezone.now()
                user.save()
                send_otp_email(user.email, otp)
                messages.info(request, 'Your email is not verified. A new verification code has been sent.')
                return redirect('verify_otp')

            auth_login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'core/login.html')

def generate_ticket_number():
    max_attempts = 10
    attempts = 0

    while attempts < max_attempts:
        prefix = ''.join(random.choices(string.ascii_uppercase, k=2))
        number = ''.join(random.choices(string.digits, k=6))
        ticket_number = f"{prefix}{number}"

        with transaction.atomic():
            if not Ticket.objects.filter(ticket_number=ticket_number).exists():
                return ticket_number
        
        attempts += 1
    
    return f"TX{uuid_module.uuid4().hex[:8].upper()}"


def ensure_ticket_integrity(ticket):
    """
    Ensures a ticket has all required fields for proper functioning.
    This function can be called to fix tickets on-the-fly.
    """
    updated = False
    
    if not ticket.unique_id:
        ticket.unique_id = uuid_module.uuid4()
        updated = True
    
    if not ticket.unique_secure_token:
        ticket.unique_secure_token = str(uuid_module.uuid4())
        updated = True
    
    if not ticket.ticket_number:
        ticket.ticket_number = generate_ticket_number()
        updated = True
    
    if updated:
        ticket.save()
    
    return updated

@login_required
def get_event_ticket_types(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    ticket_types = []
    
    if event.remaining_attendee_capacity > 0:
        for ticket_type in event.ticket_types.all():
            available = event.remaining_attendee_capacity // ticket_type.attendees_per_ticket
            
            if available > 0:
                ticket_types.append({
                    'id': ticket_type.id,
                    'type_name': ticket_type.type_name,
                    'price': float(ticket_type.price),
                    'description': ticket_type.description,
                    'attendees_per_ticket': ticket_type.attendees_per_ticket,
                    'available': available
                })
    
    if request.POST.get('book_tickets'):
        return redirect('checkout', event_id=event_id)
    
    return JsonResponse({'ticket_types': ticket_types})

@login_required
def book_ticket(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    ticket_types = TicketType.objects.filter(event=event)
    
    ticket_types_with_availability = []
    for ticket_type in ticket_types:
        attendees_per_ticket = ticket_type.attendees_per_ticket or 1
        max_possible_tickets = event.remaining_attendee_capacity // attendees_per_ticket
        if max_possible_tickets < 0:
            max_possible_tickets = 0
        ticket_type.available_quantity = max_possible_tickets
        ticket_types_with_availability.append(ticket_type)
    
    if request.method == 'POST':
        selected_tickets = []
        total_amount = 0
        total_attendees_requested = 0
        
        for key, value in request.POST.items():
            if key.startswith('ticket_') and value.isdigit() and int(value) > 0:
                ticket_type_id = key.split('_')[1]
                quantity = int(value)
                
                try:
                    ticket_type = TicketType.objects.get(id=ticket_type_id, event=event)
                    
                    attendees_per_ticket = ticket_type.attendees_per_ticket or 1
                    attendees_for_this_type = quantity * attendees_per_ticket
                    total_attendees_requested += attendees_for_this_type
                    
                    subtotal = float(ticket_type.price) * quantity
                        
                    selected_tickets.append({
                        'id': ticket_type.id,
                        'type_name': ticket_type.type_name,
                        'price': float(ticket_type.price),
                        'quantity': quantity,
                        'attendees_per_ticket': attendees_per_ticket,
                        'subtotal': subtotal,
                        'total_attendees': attendees_for_this_type
                    })
                    total_amount += subtotal
                except TicketType.DoesNotExist:
                    messages.error(request, 'Invalid ticket type selected.')
                    return redirect('book_ticket', event_id=event_id)
        
        if not selected_tickets:
            messages.error(request, 'Please select at least one ticket.')
            return redirect('book_ticket', event_id=event_id)
        
        if total_attendees_requested > event.remaining_attendee_capacity:
            messages.error(request, f'Not enough capacity. Only {event.remaining_attendee_capacity} attendees can be registered.')
            return redirect('book_ticket', event_id=event_id)
        
        request.session['ticket_order'] = {
            'event_id': event_id,
            'ticket_types': selected_tickets,
            'subtotal': total_amount,
            'total': total_amount,
            'total_attendees': total_attendees_requested
        }
        
        return redirect('checkout', event_id=event_id)
    
    context = {
        'event': event,
        'ticket_types': ticket_types_with_availability,
    }
    return render(request, 'core/ticket_booking.html', context)

def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.role = 'CUSTOMER'  # Set role for self-registration
            otp = generate_otp()
            user.email_verification_otp = otp
            user.email_verification_otp_created_at = timezone.now()
            user.set_password(form.cleaned_data.get('password1'))
            user.save()
            send_otp_email(user.email, otp)
            request.session['user_pk_for_verification'] = user.pk
            messages.success(request, 'A verification code has been sent to your email.')
            return redirect('verify_otp')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/signup.html', {'form': form})

def verify_otp_view(request):
    user_pk = request.session.get('user_pk_for_verification')
    if not user_pk:
        messages.error(request, 'Could not find a user to verify. Please sign up or log in again.')
        return redirect('signup')

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        messages.error(request, 'User not found. Please sign up again.')
        return redirect('signup')

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data.get('otp')

            if user.email_verification_otp_created_at and timezone.now() > user.email_verification_otp_created_at + timedelta(minutes=10):
                messages.error(request, 'OTP has expired. A new code has been sent.')
                otp = generate_otp()
                user.email_verification_otp = otp
                user.email_verification_otp_created_at = timezone.now()
                user.save()
                send_otp_email(user.email, otp)
                return render(request, 'core/verify_otp.html', {'form': OTPForm()})

            if user.email_verification_otp == entered_otp:
                user.email_verified = True
                user.email_verification_otp = None
                user.email_verification_otp_created_at = None
                user.save()

                if 'user_pk_for_verification' in request.session:
                    del request.session['user_pk_for_verification']

                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'Email verified successfully! You are now logged in.')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
    else:
        form = OTPForm()

    return render(request, 'core/verify_otp.html', {'form': form})

@login_required
def dashboard(request):
    context = {
        'user': request.user,
        'now': timezone.now(),  # Add current timestamp for display
    }
    
    if request.user.role == 'ADMIN':
        context.update({
            'total_users': User.objects.count(),
            'total_events': Event.objects.count(),
            'total_tickets': Ticket.objects.count(),
        })
        template = 'core/admin_dashboard.html'
    
    elif request.user.role == 'ORGANIZER':
        # Get all events organized by this user (both direct ownership and through EventStaff model)
        direct_events = list(Event.objects.filter(organizer=request.user).prefetch_related('ticket_types'))
        staff_events = list(Event.objects.filter(staff__user=request.user, staff__role='ORGANIZER').prefetch_related('ticket_types'))
        
        # Combine both sets of events (removing duplicates by ID)
        event_ids = set()
        events = []
        for event in direct_events + staff_events:
            if event.id not in event_ids:
                events.append(event)
                event_ids.add(event.id)
        
        context['events'] = events
        
        # Calculate total revenue, tickets sold, and total attendees
        total_revenue = 0
        total_tickets_sold = 0
        total_attendees = 0
        
        # Data for charts
        revenue_by_date = {}
        tickets_by_type = {}
        event_names = []
        total_tickets_list = []
        checked_in_tickets_list = []
        
        # Additional data structures for enhanced dashboard
        event_revenues = {}
        event_checkins = {}
        
        # Get date range for comparison metrics
        today = timezone.now().date()
        one_week_ago = today - timedelta(days=7)
        one_month_ago = today - timedelta(days=30)
        
        # Metrics for comparison (last week/month)
        tickets_last_week = 0
        tickets_this_week = 0
        revenue_last_month = 0
        revenue_this_month = 0
        
        # Activity log for recent activities (would be from a real activity model in production)
        recent_activities = [
            {
                'action': 'Downloaded attendee report',
                'timestamp': timezone.now() - timedelta(hours=3)
            },
            {
                'action': 'Created new event',
                'timestamp': timezone.now() - timedelta(days=2)
            },
            {
                'action': 'Updated ticket prices',
                'timestamp': timezone.now() - timedelta(days=5)
            }
        ]
        
        for event in events:
            # Get sold tickets for this event
            sold_tickets = Ticket.objects.filter(event=event, status='SOLD').select_related('ticket_type')
            event_revenue = sum(ticket.ticket_type.price for ticket in sold_tickets if ticket.ticket_type)
            total_revenue += event_revenue
            
            # Store revenue per event for the table
            event_revenues[event.id] = event_revenue
            
            # Count tickets and attendees
            event_tickets_sold = sold_tickets.count()
            total_tickets_sold += event_tickets_sold
            
            # Calculate total attendees (based on ticket types)
            event_attendees = 0
            for ticket in sold_tickets:
                if ticket.ticket_type and ticket.ticket_type.attendees_per_ticket:
                    event_attendees += ticket.ticket_type.attendees_per_ticket
                else:
                    event_attendees += 1  # Default to 1 if not specified
                
                # Calculate comparative metrics
                if ticket.purchase_date:
                    purchase_date = ticket.purchase_date.date()
                    # For weekly comparison
                    if one_week_ago <= purchase_date < today:
                        tickets_this_week += 1
                    elif purchase_date < one_week_ago:
                        tickets_last_week += 1
                    
                    # For monthly revenue comparison
                    if one_month_ago <= purchase_date < today and ticket.ticket_type:
                        revenue_this_month += float(ticket.ticket_type.price)
                    elif purchase_date < one_month_ago and ticket.ticket_type:
                        revenue_last_month += float(ticket.ticket_type.price)
            
            total_attendees += event_attendees
            
            # Process ticket data for charts
            for ticket in sold_tickets:
                # For sales over time
                purchase_date = ticket.purchase_date.date() if ticket.purchase_date else timezone.now().date()
                date_str = purchase_date.strftime('%Y-%m-%d')
                if date_str not in revenue_by_date:
                    revenue_by_date[date_str] = 0
                if ticket.ticket_type:
                    revenue_by_date[date_str] += float(ticket.ticket_type.price)
                
                # For ticket type breakdown
                if ticket.ticket_type:
                    type_id = ticket.ticket_type.id
                    type_name = ticket.ticket_type.type_name
                    if type_id not in tickets_by_type:
                        tickets_by_type[type_id] = {
                            'name': type_name,
                            'count': 0
                        }
                    tickets_by_type[type_id]['count'] += 1
            
            # For attendance chart
            event_names.append(event.title)
            total_tickets_list.append(event_tickets_sold)
            checked_in = Ticket.objects.filter(event=event, status='USED').count()
            checked_in_tickets_list.append(checked_in)
            
            # Store check-ins per event for the check-in progress section
            event_checkins[event.id] = checked_in
        
        # Sort and format date data for revenue chart
        revenue_dates = sorted(revenue_by_date.keys())
        revenue_amounts = [revenue_by_date[date] for date in revenue_dates]
        
        # Format dates for display
        formatted_dates = []
        for date_str in revenue_dates:
            try:
                date_obj = dt.strptime(date_str, '%Y-%m-%d')
                formatted_dates.append(date_obj.strftime('%b %d'))
            except ValueError:
                # In case of invalid date string, use a placeholder
                formatted_dates.append('Unknown')
        
        # Calculate percentage changes for comparative metrics
        tickets_change = 0
        if tickets_last_week > 0:
            tickets_change = round((tickets_this_week - tickets_last_week) / tickets_last_week * 100)
            
        revenue_change = 0
        if revenue_last_month > 0:
            revenue_change = round((revenue_this_month - revenue_last_month) / revenue_last_month * 100)
            
        # Calculate check-in percentage
        checked_in_percentage = None
        if total_tickets_sold > 0:
            checked_in_percentage = round(sum(checked_in_tickets_list) / total_tickets_sold * 100)
        
        # Add chart data and new metrics to context
        context.update({
            'total_revenue': total_revenue,
            'total_tickets_sold': total_tickets_sold,
            'total_attendees': total_attendees,
            'revenue_dates': formatted_dates,
            'revenue_amounts': revenue_amounts,
            'ticket_types_data': list(tickets_by_type.values()),
            'event_names': event_names,
            'total_tickets': total_tickets_list,
            'checked_in_tickets': checked_in_tickets_list,
            # New context variables for enhanced dashboard
            'event_revenues': event_revenues,
            'event_checkins': event_checkins,
            'tickets_change': tickets_change,
            'revenue_change': revenue_change,
            'checked_in_percentage': checked_in_percentage,
            'recent_activities': recent_activities
        })
        
        template = 'core/organizer_dashboard.html'
    
    elif request.user.role == 'VOLUNTEER':
        # Redirect volunteers to their specific dashboard
        return redirect('volunteer_dashboard')
    
    elif request.user.role == 'CUSTOMER':
        context['tickets'] = Ticket.objects.filter(
            customer=request.user, 
            status='SOLD'
        ).select_related('event', 'ticket_type').order_by('-purchase_date')
        
        today = timezone.now().date()
        events = Event.objects.filter(
            status='PUBLISHED', 
            date__gte=today
        ).prefetch_related('ticket_types').order_by('date')
        events_with_prices = []
        
        for event in events:
            min_price = float('inf')
            for ticket_type in event.ticket_types.all():
                if ticket_type.price < min_price:
                    min_price = ticket_type.price
            events_with_prices.append({
                'event': event,
                'min_price': min_price if min_price != float('inf') else None,
                'tickets_are_live': event.tickets_are_live
            })
            
        context['events'] = events_with_prices
        template = 'core/customer_dashboard.html'
    else:
        template = 'core/dashboard.html'
        
    return render(request, template, context)

@login_required
@user_passes_test(is_organizer)
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm()
    return render(request, 'core/create_event.html', {'form': form})

def event_list(request):
    events_with_prices = get_event_data()
    return render(request, 'core/event_list.html', {'events_with_prices': events_with_prices})

def event_detail(request, event_id):
    event = get_object_or_404(Event.objects.prefetch_related('ticket_types'), id=event_id)
    
    ticket_types = []
    
    for ticket_type in event.ticket_types.all():
        max_possible_tickets = event.remaining_attendee_capacity // ticket_type.attendees_per_ticket
        
        ticket_types.append({
            'type': ticket_type,
            'available_count': max_possible_tickets
        })
    
    context = {
        'event': event,
        'ticket_types': ticket_types,
        'remaining_attendee_capacity': event.remaining_attendee_capacity,
        'next': request.path,
    }
    return render(request, 'core/event_detail.html', context)

@login_required
def checkout(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    ticket_order = request.session.get('ticket_order', {})
    
    if not ticket_order or ticket_order.get('event_id') != event_id:
        messages.error(request, 'No ticket order found. Please select tickets first.')
        return redirect('event_detail', event_id=event_id)
    
    selected_tickets = ticket_order.get('ticket_types', [])
    subtotal = ticket_order.get('subtotal', 0)
    
    if request.method == 'POST':
        applied_promo_code = request.POST.get('promo_code', '').strip()
        total = subtotal
        discount = 0

        if applied_promo_code:
            try:
                promo = PromoCode.objects.get(code=applied_promo_code, event=event)
                if promo.is_valid:
                    if promo.discount_type == 'PERCENTAGE':
                        discount = (float(promo.discount_value) / 100) * subtotal
                    else:
                        discount = min(float(promo.discount_value), subtotal)
                    
                    total = subtotal - discount
                    request.session['ticket_order']['discount'] = float(discount)
                    request.session['ticket_order']['promo_code'] = applied_promo_code
                else:
                    messages.error(request, 'The promo code is no longer valid.')
                    request.session['ticket_order']['discount'] = 0
                    request.session['ticket_order']['promo_code'] = ''
            except PromoCode.DoesNotExist:
                messages.error(request, 'Invalid promo code entered.')
                request.session['ticket_order']['discount'] = 0
                request.session['ticket_order']['promo_code'] = ''
        else:
            request.session['ticket_order']['discount'] = 0
            request.session['ticket_order']['promo_code'] = ''
            
        request.session['ticket_order']['total'] = total
        request.session.modified = True
        
    discount = request.session.get('ticket_order', {}).get('discount', 0)
    promo_code = request.session.get('ticket_order', {}).get('promo_code', '')
    total = request.session.get('ticket_order', {}).get('total', subtotal)
    
        

    
    total_attendees = ticket_order.get('total_attendees', 0)

    context = {
        'event': event,
        'ticket_types': selected_tickets,
        'subtotal': subtotal,
        'total': total,
        'discount': discount,
        'promo_code': promo_code,
        'user': request.user,
        'total_attendees': total_attendees,
        'show_service_fee': False,  # Flag to control template display
        'debug': settings.DEBUG,  # Pass debug flag for environment detection
    }
    return render(request, 'core/checkout_new.html', context)

@require_GET
def validate_promo_code(request, code):
    event_id = request.GET.get('event_id')
    if not event_id:
        return JsonResponse({'valid': False, 'message': 'Event ID is required'})
        
    if not code or code.strip() == '':
        return JsonResponse({'valid': False, 'message': 'Please enter a promo code'})
    
    # Check if the same code is already stored in the session and is valid
    stored_promo = request.session.get('ticket_order', {}).get('promo_code', '')
    if stored_promo == code and request.session.get('ticket_order', {}).get('discount', 0) > 0:
        # Return existing discount data from session
        discount = request.session['ticket_order']['discount']
        final_total = request.session['ticket_order']['total']
        subtotal = request.session['ticket_order'].get('subtotal', 0)
        
        return JsonResponse({
            'valid': True,
            'discount': round(float(discount), 2),
            'final_total': round(float(final_total), 2),
            'message': f'Promo code applied successfully!'
        })
        
    try:
        promo = PromoCode.objects.get(code=code, event_id=event_id)
        
        if not promo.is_valid:
            now = timezone.now()
            if not promo.is_active: message = 'This promo code is inactive'
            elif promo.valid_from > now: message = 'This promo code is not yet valid'
            elif promo.valid_until < now: message = 'This promo code has expired'
            elif promo.max_uses > 0 and promo.current_uses >= promo.max_uses: message = 'This promo code has reached its maximum usage limit'
            else: message = 'This promo code is no longer valid'
            return JsonResponse({'valid': False, 'message': message})
            
        order_total = request.session.get('ticket_order', {}).get('subtotal', 0)
        if order_total == 0:
            return JsonResponse({'valid': False, 'message': 'No order total available for discount calculation'})
            
        if promo.discount_type == 'PERCENTAGE':
            discount = (float(promo.discount_value) / 100) * order_total
            discount_text = f"{promo.discount_value}% off"
        else:
            discount = min(float(promo.discount_value), order_total)
            discount_text = f"₹{promo.discount_value} off"
            
        final_total = max(0, order_total - discount)
        
        request.session['ticket_order']['total'] = final_total
        request.session['ticket_order']['discount'] = discount
        request.session['ticket_order']['promo_code'] = code
        request.session.modified = True
        
        return JsonResponse({
            'valid': True,
            'discount': round(float(discount), 2),
            'final_total': round(float(final_total), 2),
            'discount_text': discount_text,
            'message': f'Promo code applied successfully! {discount_text}'
        })
    except PromoCode.DoesNotExist:
        return JsonResponse({'valid': False, 'message': 'Invalid promo code'})
    except Exception as e:
        logger.error(f"Error validating promo code: {str(e)}")
        return JsonResponse({'valid': False, 'message': f'An unexpected error occurred.'})

@login_required
@user_passes_test(is_customer)
def purchase_ticket(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    ticket = Ticket.objects.filter(event=event, status='AVAILABLE').first()
    
    if ticket:
        ticket.customer = request.user
        ticket.status = 'SOLD'
        ticket.save()
        messages.success(request, 'Ticket purchased successfully!')
        return redirect('dashboard')
    else:
        messages.error(request, 'No tickets available for this event.')
        return redirect('event_detail', event_id=event.id)



@login_required
@user_passes_test(is_admin)
def manage_event_staff(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = EventStaffForm(request.POST)
        if form.is_valid():
            staff = form.save(commit=False)
            staff.event = event
            staff.save()
            messages.success(request, f'{staff.role} added successfully!')
            return redirect('event_detail', event_id=event.id)
    else:
        volunteer_form = EventStaffForm(initial={'role': 'VOLUNTEER'})
        organizer_form = EventStaffForm(initial={'role': 'ORGANIZER'})
    
    current_staff = EventStaff.objects.filter(event=event)
    return render(request, 'core/manage_event_staff.html', {
        'event': event,
        'volunteer_form': volunteer_form,
        'organizer_form': organizer_form,
        'current_staff': current_staff
    })

@login_required
@user_passes_test(is_admin)
def manage_promo_codes(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = PromoCodeForm(request.POST)
        if form.is_valid():
            promo = form.save(commit=False)
            promo.event = event
            promo.save()
            messages.success(request, 'Promo code created successfully!')
            return redirect('manage_promo_codes', event_id=promo.event.id)
    else:
        form = PromoCodeForm()
    
    promo_codes = PromoCode.objects.filter(event=event)
    return render(request, 'core/manage_promo_codes.html', {
        'event': event,
        'form': form,
        'promo_codes': promo_codes
    })

@login_required
@user_passes_test(is_admin)
def toggle_promo_code(request, code_id):
    promo = get_object_or_404(PromoCode, id=code_id)
    promo.is_active = not promo.is_active
    promo.save()
    messages.success(request, f'Promo code {promo.code} {"activated" if promo.is_active else "deactivated"} successfully!')
    return redirect('manage_promo_codes', event_id=promo.event.id)

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('dashboard')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'core/update_profile.html', {'form': form})

@login_required
def process_payment(request, event_id):
    # Simulate interaction with payment gateway
    payment_response = get_payment_gateway_response(event_id)

    if payment_response.get('status') == 'SUCCESS':
        # Payment successful
        Ticket.objects.filter(event_id=event_id, customer=request.user).update(status='SOLD')
        return redirect('payment_success')
    else:
        # Payment failed
        failure_reason = payment_response.get('failure_reason', 'UNKNOWN')
        return redirect('payment_failed', event_id=event_id, failure_reason=failure_reason)

@login_required
def checkout_success(request, event_id=None):
    recent_tickets = Ticket.objects.filter(
        customer=request.user, 
        status='SOLD'
    ).select_related('event', 'ticket_type').order_by('-purchase_date')[:5]
    
    context = {
        'recent_tickets': recent_tickets,
        'user': request.user
    }
    
    return render(request, 'core/checkout_success.html', context)

# Admin Event Management Views






# Ticket checkout and download API functions
@require_http_methods(["POST"])
def api_checkout_ticket(request):
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        ticket_type_id = data.get('ticket_type_id')
        
        if not user_id or not ticket_type_id:
            return JsonResponse({'success': False, 'message': 'Missing required data'}, status=400)
            
        user = get_object_or_404(User, id=user_id)
        ticket_type = get_object_or_404(TicketType, id=ticket_type_id)
        event = ticket_type.event
        
        if event.remaining_attendee_capacity < ticket_type.attendees_per_ticket:
            return JsonResponse({'success': False, 'message': 'Insufficient event capacity'}, status=400)
        
        ticket_number = generate_ticket_number()
        unique_secure_token = str(uuid_module.uuid4())
        
        ticket = Ticket.objects.create(
            user=user,
            event=event,
            ticket_type=ticket_type,
            price=ticket_type.price,
            purchase_date=timezone.now(),
            unique_secure_token=unique_secure_token,
            unique_id=uuid_module.uuid4()  # Ensure unique_id is set
        )
        
        return JsonResponse({
            'success': True,
            'ticket_id': ticket.id,
            'ticket_number': ticket.ticket_number,
            'event_name': event.title,
            'ticket_type': ticket_type.type_name,
            'event_date': event.date.strftime('%B %d, %Y'),
            'event_time': event.time.strftime('%I:%M %p'),
            'venue': event.venue,
            'attendees': ticket_type.attendees_per_ticket,
            'message': 'Ticket created successfully'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error creating ticket: {str(e)}'}, status=500)

@login_required
@require_http_methods(["GET"])
def event_pass(request, ticket_id):
    try:
        ticket = get_object_or_404(Ticket, id=ticket_id)
        # Permission check
        if request.user != ticket.customer and request.user.role != 'ADMIN':
            messages.error(request, 'You do not have permission to view this ticket.')
            return redirect('my_tickets')

        # Ensure ticket has all required fields
        ensure_ticket_integrity(ticket)

        # Generate QR code as base64
        qr_data = create_signed_ticket_data(ticket)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=0,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
        buffered = BytesIO()
        qr_img.save(buffered, format="PNG")
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Sponsor logos as list of URLs
        sponsor_logos_list = []
        try:
            if hasattr(ticket.event, 'sponsors'):
                sponsor_logos_list = [s.get_logo_url() for s in ticket.event.sponsors.all() if s.get_logo_url()]
        except Exception as e:
            logger.warning(f"Error fetching sponsor logos: {e}")

        # Prepare venue display with fallback
        venue_display = ticket.event.venue.upper() if ticket.event.venue else "VENUE TBA"
        
        context = {
            'event_name': ticket.event.title,
            'event_subtitle': '- The Beginning -',  # Fixed subtitle, not from database
            'event_datetime': f"{ticket.event.date.strftime('%d %b %Y').upper()}, {ticket.event.time.strftime('%I:%M %p')} ONWARDS",
            'event_venue': venue_display,  # Dynamic venue from event with fallback
            'event_venue_address': ticket.event.venue_address or '',  # Venue address with fallback
            'pass_type': ticket.ticket_type.type_name.upper() if ticket.ticket_type else 'GENERAL',
            'admit_count': ticket.total_admission_count,  # Use consolidated admission count
            'booking_quantity': ticket.booking_quantity,  # Add booking quantity for display
            'attendees_per_ticket': ticket.ticket_type.attendees_per_ticket if ticket.ticket_type else 1,  # Attendees per individual ticket
            'qr_code_url': f"data:image/png;base64,{qr_code_base64}",
            'ticket_id': ticket.ticket_number,
            'event_date': ticket.event.date,  # Raw date object
            'event_time': ticket.event.time,  # Raw time object
            'event_description': ticket.event.description,  # Full event description
            'event_type': ticket.event.event_type,  # Event type
            'ticket_status': ticket.status,  # Ticket status
            'purchase_date': ticket.purchase_date,  # When ticket was purchased
            'event_organizer': ticket.event.organizer.get_full_name() if ticket.event.organizer else 'Event Organizer',  # Organizer name
            'sponsor_logos_list': sponsor_logos_list,
            'event': ticket.event,  # Pass the entire event object to access sponsors relation
        }
        return render(request, 'animated_pass_template.html', context)
    except Exception as e:
        messages.error(request, f'Error generating event pass: {str(e)}')
        return redirect('my_tickets')

def api_download_ticket(request, ticket_id):
    try:
        ticket = get_object_or_404(Ticket, id=ticket_id)
        
        if request.user != ticket.customer and request.user.role != 'ADMIN':
            return JsonResponse({'success': False, 'message': 'Unauthorized access'}, status=403)
        
        ticket_type = ticket.ticket_type
        
        if not ticket_type:
            return JsonResponse({'success': False, 'message': 'Ticket type not available'}, status=400)
            
        try:
            ticket_image = generate_ticket_image(ticket)
            
            buffered = BytesIO()
            ticket_image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return JsonResponse({
                'success': True,
                'ticket_image': img_str,
                'ticket_number': ticket.ticket_number,
                'ticket_id': ticket.id,
            })
        except Exception as e:
            logger.error(f"Error generating ticket image: {str(e)}")
            return JsonResponse({'success': False, 'message': f'Error generating ticket image: {str(e)}'}, status=500)
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error generating ticket: {str(e)}'}, status=500)

def generate_ticket_image(ticket):
    # --- New PNG Ticket Design ---
    event = ticket.event
    ticket_type = ticket.ticket_type
    width, height = 1200, 500
    bg_color = (31, 41, 55)  # #1f2937 dark gray
    right_bg_color = (55, 65, 81)  # #374151
    white = (255, 255, 255)
    accent = (75, 85, 99)  # #4b5563
    blue = (156, 234, 239)
    # Create base image
    img = Image.new('RGBA', (width, height), color=white)
    draw = ImageDraw.Draw(img)
    # Left section (main info)
    left_w = int(width * 0.66)
    draw.rectangle([0, 0, left_w, height], fill=bg_color)
    # Right section (QR and admit)
    draw.rectangle([left_w, 0, width, height], fill=right_bg_color)
    # Perforated line
    for y in range(0, height, 20):
        draw.rectangle([left_w-2, y, left_w, y+10], fill=accent)
    # Fonts
    def load_font(size, bold=False):
        try:
            if bold:
                return ImageFont.truetype("arialbd.ttf", size)
            return ImageFont.truetype("arial.ttf", size)
        except:
            return ImageFont.load_default()
    font_title = load_font(60, bold=True)
    font_subtitle = load_font(32)
    font_label = load_font(20)
    font_value = load_font(28, bold=True)
    font_small = load_font(18)
    font_xs = load_font(14)
    # Event Name
    draw.text((40, 40), event.title, font=font_title, fill=white)
    # Subtitle
    draw.text((40, 120), "- The Beginning -", font=font_subtitle, fill=blue)
    # Date & Time
    draw.text((40, 180), "DATE & TIME", font=font_label, fill=accent)
    dt_str = f"{event.date.strftime('%d %b %Y').upper()}, {event.time.strftime('%I:%M %p')} ONWARDS"
    draw.text((250, 180), dt_str, font=font_value, fill=white)
    # Venue
    draw.text((40, 220), "VENUE", font=font_label, fill=accent)
    draw.text((250, 220), "LUX PUB & KITCHEN, KORAMANGALA", font=font_value, fill=white)
    # Sponsors
    draw.text((40, 270), "SPONSORS", font=font_label, fill=accent)
    # Sponsor logos (up to 3, 60x60px)
    sponsor_x = 250
    sponsor_y = 265
    sponsor_size = 60
    if hasattr(event, 'sponsors'):
        sponsors = [s for s in event.sponsors.all() if hasattr(s, 'get_logo_url') and s.get_logo_url()]
        for i, sponsor in enumerate(sponsors[:3]):
            try:
                import requests
                from io import BytesIO as BIO
                resp = requests.get(sponsor.get_logo_url(), timeout=2)
                logo_img = Image.open(BIO(resp.content)).convert('RGBA').resize((sponsor_size, sponsor_size))
                img.paste(logo_img, (sponsor_x + i*(sponsor_size+20), sponsor_y), logo_img)
            except Exception as e:
                logger.warning(f"Could not load sponsor logo: {e}")
    # Ticketing Partner
    draw.text((40, 350), "TICKETING PARTNER", font=font_label, fill=accent)
    draw.text((250, 350), "TAPNEX", font=font_value, fill=blue)
    # Right section: Pass type, admit, QR, ticket id
    right_x = left_w + 40
    # Pass type
    pass_type = ticket_type.type_name.upper() if ticket_type else ''
    draw.text((right_x, 40), pass_type, font=font_value, fill=white)
    # Admit count
    draw.text((right_x, 110), "ADMIT", font=font_label, fill=accent)
    admit_count = str(ticket_type.attendees_per_ticket if ticket_type else 1)
    draw.text((right_x, 140), admit_count, font=font_title, fill=white)
    # QR code
    if not ticket.unique_secure_token:
        unique_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        ticket.unique_secure_token = unique_id
        ticket.save()
    qr_data = create_signed_ticket_data(ticket)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=0,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
    qr_size = 180
    qr_pos = (right_x, 220)
    qr_img = qr_img.resize((qr_size, qr_size))
    img.paste(qr_img, qr_pos, qr_img)
    # Ticket ID
    ticket_id = ticket.ticket_number
    draw.text((right_x, 420), f"ID: {ticket_id}", font=font_small, fill=blue)
    # Footer note
    draw.text((right_x, 460), "This ticket is non-transferable. Management reserves the right of admission.", font=font_xs, fill=accent)
    return img

def create_signed_ticket_data(ticket):
    """Create signed ticket data for QR code"""
    if not ticket.ticket_number or len(ticket.ticket_number) < 6:
        ticket.ticket_number = f"{ticket.event.id:02d}-{random.randint(100000, 999999)}"
        ticket.save()
    
    if not ticket.unique_secure_token:
        unique_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        ticket.unique_secure_token = unique_id
        ticket.save()
    
    timestamp = int(timezone.now().timestamp())
    
    # Create ticket data in the compact format that the scanner expects
    ticket_data = {
        'tid': ticket.id,  # Compact name for ticket_id
        'tok': ticket.unique_secure_token,  # Compact name for token
        'ts': timestamp,   # Timestamp
    }
    
    # Create signature
    secret_key = settings.SECRET_KEY.encode()
    message = f"{ticket.id}:{ticket.unique_secure_token}:{timestamp}".encode()
    signature = hmac.new(secret_key, message, hashlib.sha256).hexdigest()[:16]
    ticket_data['sig'] = signature
    
    return json.dumps(ticket_data)
    
# Pages for footer links
def contact(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Create email content for the contact form submission
        email_subject = f"Contact Form: {subject}"
        email_body = f"""
New contact form submission from TapNex website:

Name: {first_name} {last_name}
Email: {email}
Phone: {phone if phone else 'Not provided'}
Subject: {subject}

Message:
{message}

---
This email was sent from the TapNex contact form.
        """
        
        # Send email to info@tapnex.tech using the reliable email backend
        try:
            from .utils import send_email_with_retry
            
            email_sent = send_email_with_retry(
                subject=email_subject,
                message=email_body,
                from_email=email,  # Use customer's email as from address
                recipient_list=['tapnex.fc@gmail.com'],
            )
            
            if email_sent:
                messages.success(request, "Thank you for your message! We've received it and will get back to you soon.")
            else:
                messages.error(request, "There was an issue sending your message. Please try again or email us directly at info@tapnex.tech")
                
        except Exception as e:
            messages.error(request, "There was an issue sending your message. Please try again or email us directly at info@tapnex.tech")
            logger.error(f"Contact form email error: {str(e)}")
            
        return redirect('contact')
    
    return render(request, 'core/contact.html')

def terms(request):
    return render(request, 'core/terms.html')

def refunds(request):
    return render(request, 'core/refunds.html')

def test_static_files(request):
    """Test page for static files verification"""
    return render(request, 'static_test.html')

def privacy(request):
    return render(request, 'core/privacy.html')


@login_required
def send_ticket_email(request, ticket_id):
    """
    Sends an email with a link to the online ticket pass.
    """
    try:
        ticket = get_object_or_404(Ticket, id=ticket_id)
        # Security check: Ensure the user owns the ticket or is an admin
        if request.user != ticket.customer and not request.user.is_staff:
            messages.error(request, 'You do not have permission to access this ticket.')
            return redirect('my_tickets')

        # Build the pass URL (secure, only for owner)
        # Use production domain instead of request domain to avoid testserver issues
        from django.conf import settings
        if hasattr(settings, 'SITE_DOMAIN'):
            base_url = settings.SITE_DOMAIN
        elif not settings.DEBUG:
            # Production - use the production domain
            base_url = 'https://tickets.tapnex.tech'
        else:
            # Development - fallback to request domain but prefer localhost
            if 'testserver' in request.get_host():
                base_url = 'http://localhost:8000'
            else:
                base_url = request.build_absolute_uri('/').rstrip('/')
        
        pass_url = f"{base_url}{reverse('view_online_ticket', kwargs={'unique_id': ticket.unique_id})}"

        context = {
            'event_name': ticket.event.title,
            'ticket_url': pass_url,
        }

        # Render the email template
        email_body_html = render_to_string('email/ticket_confirmation_link.html', context)
        subject = f"Your Event Pass for {ticket.event.title}"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = ticket.customer.email

        email = EmailMessage(
            subject,
            email_body_html,
            from_email,
            [to_email],
        )
        email.content_subtype = "html"
        email.send()
        messages.success(request, 'Your event pass email has been sent! Please check your inbox.')
        logger.info(f"Successfully sent event pass email (view online) for ticket {ticket_id} to {to_email}")
    except Exception as e:
        logger.error(f"Error in send_ticket_email for ticket_id {ticket_id}: {str(e)}")
        logger.error(traceback_module.format_exc())
        messages.error(request, 'An unexpected error occurred while sending your ticket. Please contact support.')
    return redirect('my_tickets')


def send_ticket_confirmation_email(ticket, request):
    """
    Sends an automatic ticket confirmation email with online pass link after successful payment.
    This is called automatically during payment processing.
    """
    try:
        # Build the pass URL (secure, only for owner)
        # Use production domain instead of request domain to avoid testserver issues
        from django.conf import settings
        if hasattr(settings, 'SITE_DOMAIN'):
            base_url = settings.SITE_DOMAIN
        elif not settings.DEBUG:
            # Production - use the production domain
            base_url = 'https://tickets.tapnex.tech'
        else:
            # Development - fallback to request domain but prefer localhost
            if 'testserver' in request.get_host():
                base_url = 'http://localhost:8000'
            else:
                base_url = request.build_absolute_uri('/').rstrip('/')
        
        pass_url = f"{base_url}{reverse('view_online_ticket', kwargs={'unique_id': ticket.unique_id})}"

        context = {
            'event_name': ticket.event.title,
            'ticket_url': pass_url,
            'customer_name': ticket.customer.first_name or ticket.customer.email,
            'ticket_number': ticket.ticket_number,
        }

        # Render the email template
        email_body_html = render_to_string('email/ticket_confirmation_link.html', context)
        subject = f"🎫 Your Ticket Confirmation for {ticket.event.title}"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = ticket.customer.email

        email = EmailMessage(
            subject,
            email_body_html,
            from_email,
            [to_email],
        )
        email.content_subtype = "html"
        email.send()
        
        logger.info(f"Successfully sent ticket confirmation email for ticket {ticket.ticket_number} to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Error in send_ticket_confirmation_email for ticket {ticket.ticket_number}: {str(e)}")
        logger.error(traceback_module.format_exc())
        return False


def view_online_ticket(request, unique_id):
    """
    This view displays the animated, responsive event pass online.
    """
    try:
        ticket = get_object_or_404(Ticket, unique_id=unique_id)
        
        # Ensure ticket has all required fields
        ensure_ticket_integrity(ticket)
        
        # Generate QR code as base64
        qr_data = create_signed_ticket_data(ticket)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        qr_code_data_url = f"data:image/png;base64,{qr_code_base64}"
    
        # Prepare sponsor logos
        sponsor_logos_list = []
        try:
            if hasattr(ticket.event, 'sponsors'):
                sponsor_logos_list = [s.get_logo_url() for s in ticket.event.sponsors.all() if s.get_logo_url()]
        except Exception as e:
            logger.warning(f"Error fetching sponsor logos: {e}")

        # Prepare venue display with fallback
        venue_display = ticket.event.venue.upper() if ticket.event.venue else "VENUE TBA"
    
        # Build the context dictionary with data from the ticket object
        context = {
            'event_name': ticket.event.title,
            'event_subtitle': '- The Beginning -',  # Fixed subtitle, not from database
            'event_datetime': f"{ticket.event.date.strftime('%d %b %Y')}, {ticket.event.time.strftime('%I:%M %p')} ONWARDS",
            'event_venue': venue_display,  # Dynamic venue from event with fallback
            'event_venue_address': ticket.event.venue_address or '',  # Venue address with fallback
            'pass_type': ticket.ticket_type.type_name.upper() if ticket.ticket_type else 'GENERAL',
            'admit_count': ticket.total_admission_count,  # Use consolidated admission count
            'booking_quantity': ticket.booking_quantity,  # Add booking quantity for display
            'attendees_per_ticket': ticket.ticket_type.attendees_per_ticket if ticket.ticket_type else 1,  # Attendees per individual ticket
            'qr_code_url': qr_code_data_url,
            'ticket_id': ticket.ticket_number,
            'event_date': ticket.event.date,  # Raw date object
            'event_time': ticket.event.time,  # Raw time object
            'event_description': ticket.event.description,  # Full event description
            'event_type': ticket.event.event_type,  # Event type
            'ticket_status': ticket.status,  # Ticket status
            'purchase_date': ticket.purchase_date,  # When ticket was purchased
            'event_organizer': ticket.event.organizer.get_full_name() if ticket.event.organizer else 'Event Organizer',  # Organizer name
            'sponsor_logos_list': sponsor_logos_list,
            'event': ticket.event,  # Pass the entire event object to access sponsors relation
        }
        
        # Render the new animated pass template
        return render(request, 'animated_pass_template.html', context)
    
    except Exception as e:
        messages.error(request, f'Error loading ticket: {str(e)}')
        return redirect('my_tickets')


@login_required
def create_cashfree_order(request):
    if request.method == 'POST':
        try:
            print(f"DEBUG: Starting create_cashfree_order")
            ticket_order = request.session.get('ticket_order', {})
            print(f"DEBUG: Ticket order from session: {ticket_order}")
            order_amount = ticket_order.get('total')
            print(f"DEBUG: Order amount: {order_amount}")

            if not order_amount or float(order_amount) <= 0:
                print(f"DEBUG: Invalid order amount: {order_amount}")
                return JsonResponse({'error': 'Invalid order amount. Please select tickets and try again.'}, status=400)

            # Parse request data to check terms acceptance
            try:
                request_data = json.loads(request.body)
                terms_accepted = request_data.get('terms_accepted', False)
                terms_accepted_at = request_data.get('terms_accepted_at')
                print(f"DEBUG: Terms accepted: {terms_accepted}")
            except (json.JSONDecodeError, KeyError):
                terms_accepted = False
                terms_accepted_at = None
                print(f"DEBUG: Failed to parse request data, terms_accepted set to False")

            if not terms_accepted:
                print(f"DEBUG: Terms and conditions not accepted for user {request.user.id}")
                return JsonResponse({'error': 'Please accept the terms and conditions to proceed with your purchase.'}, status=400)

            user = request.user
            print(f"DEBUG: User: {user.id}")
            
            # Format customer ID with leading zeros for consistent formatting
            customer_id = f"user_{user.id:03d}"
            
            # Clean phone number to ensure it's valid
            raw_phone = user.mobile_number or ""
            cleaned_phone = re.sub(r'\D', '', raw_phone)
            # Take last 10 digits if available, otherwise use a default
            customer_phone = cleaned_phone[-10:] if len(cleaned_phone) >= 10 else "0000000000"

            customer_name = f"{user.first_name} {user.last_name}".strip() or user.email
            customer_email = user.email

            # Generate a unique order ID
            order_id = f"order_{uuid_module.uuid4().hex[:12]}"
            
            print(f"DEBUG: Creating new payment order: {order_id} for user {user.id}, amount: {order_amount}")
            
            # Create a payment transaction record to track the entire payment lifecycle
            # Set payment gateway to 'SANDBOX' if in debug mode to distinguish test transactions
            gateway_type = 'SANDBOX' if settings.DEBUG else 'Cashfree'
            payment_transaction = PaymentTransaction.objects.create(
                user=user,
                order_id=order_id,
                amount=float(order_amount),
                status='CREATED',
                payment_gateway=gateway_type,
                event_id=ticket_order.get('event_id'),
                quantity=ticket_order.get('total_attendees', 1),
                response_data={
                    'ticket_order': ticket_order,
                    'customer_id': customer_id,
                    'customer_email': customer_email,
                    'creation_timestamp': timezone.now().isoformat(),
                    'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
                    'terms_accepted': terms_accepted,
                    'terms_accepted_at': terms_accepted_at or timezone.now().isoformat(),
                    'environment': 'SANDBOX' if settings.DEBUG else 'PRODUCTION'
                }
            )
            print(f"DEBUG: Payment transaction created: {payment_transaction.id}")

            # Setup return URL with all necessary parameters for proper callback processing
            return_url = request.build_absolute_uri(reverse('payment_status')) + \
                        f"?order_id={{order_id}}&session_order_id={order_id}&" + \
                        f"payment_status={{payment_status}}&transaction_id={{transaction_id}}"

            # Create order request for Cashfree API
            create_order_request = CreateOrderRequest(
                order_amount=float(order_amount),
                order_currency="INR",
                customer_details=CustomerDetails(
                    customer_id=customer_id,
                    customer_name=customer_name,
                    customer_email=customer_email,
                    customer_phone=customer_phone,
                ),
                order_meta=OrderMeta(
                    return_url=return_url,
                    # Send server-to-server notifications to the dedicated webhook, not the user-facing callback
                    notify_url=request.build_absolute_uri(reverse('cashfree_webhook'))
                ),
                order_id=order_id
            )
            print(f"DEBUG: Create order request prepared")
            
            # Store the ticket order in the session for retrieval during payment callback
            request.session[order_id] = ticket_order
            request.session.modified = True
            print(f"DEBUG: Ticket order stored in session")

            try:
                # Make API call to create payment order
                print(f"DEBUG: Sending create order request to Cashfree for order: {order_id}")
                api_response = Cashfree().PGCreateOrder(
                    x_api_version=CASHFREE_API_VERSION,
                    create_order_request=create_order_request,
                )
                print(f"DEBUG: Cashfree API response received")
                
                # Handle API response
                if hasattr(api_response, 'data') and api_response.data:
                    # Extract and save important data from the response
                    payment_session_id = getattr(api_response.data, 'payment_session_id', None)
                    cf_order_id = getattr(api_response.data, 'order_id', None)
                    payment_link = getattr(api_response.data, 'payment_link', None)
                    
                    # Update the transaction record with API response details
                    payment_transaction.response_data = {
                        **payment_transaction.response_data,
                        'payment_session_id': payment_session_id,
                        'cf_order_id': cf_order_id,
                        'payment_link': payment_link,
                        'api_response_timestamp': timezone.now().isoformat()
                    }
                    payment_transaction.save()
                    
                    print(f"DEBUG: Cashfree order created successfully: {cf_order_id}, session: {payment_session_id}")
                    
                    # Return necessary data for frontend to initiate payment
                    response_data = {
                        "payment_session_id": payment_session_id,
                        "order_id": cf_order_id,
                        "payment_link": payment_link,
                        "debug": settings.DEBUG  # Pass debug flag to frontend for environment detection
                    }
                    return JsonResponse(response_data)
                else:
                    print(f"DEBUG: Invalid response from Cashfree for order {order_id}: {api_response}")
                    return JsonResponse({'error': 'Invalid response from payment gateway'}, status=500)

            except Exception as e:
                print(f"DEBUG: Cashfree order creation failed for order {order_id}: {str(e)}")
                import traceback
                traceback.print_exc()
                # Update transaction with error details
                payment_transaction.status = 'FAILED'
                payment_transaction.response_data = {
                    **payment_transaction.response_data,
                    'error': str(e),
                    'error_timestamp': timezone.now().isoformat()
                }
                payment_transaction.save()
                return JsonResponse({'error': f'Payment gateway error: {str(e)}'}, status=500)

        except Exception as outer_e:
            print(f"DEBUG: Outer exception in create_cashfree_order: {str(outer_e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': f'Internal server error: {str(outer_e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def payment_status(request):
    cashfree_order_id = request.GET.get('order_id')
    session_order_id = request.GET.get('session_order_id')

    # Cashfree may not substitute unknown placeholders; sanitize placeholder values like "{payment_status}"
    raw_payment_status = request.GET.get('payment_status', '')
    payment_status_param = raw_payment_status.upper()
    if ('{' in raw_payment_status) or ('}' in raw_payment_status):
        payment_status_param = ''

    raw_txn_id = request.GET.get('transaction_id', '')
    transaction_id = raw_txn_id
    if ('{' in raw_txn_id) or ('}' in raw_txn_id):
        transaction_id = ''

    # Log all received parameters for debugging
    logger.info(f"Payment callback received - order_id: {cashfree_order_id}, payment_status: {payment_status_param}, transaction_id: {transaction_id}")

    ticket_order = request.session.get(session_order_id)

    if not ticket_order:
        logger.warning(f"No ticket_order found in session for order_id: {cashfree_order_id}")
        # Instead of redirecting immediately, try to fetch payment transaction and verify status again
        try:
            payment_transaction = PaymentTransaction.objects.get(order_id=cashfree_order_id)
            logger.info(f"Found payment transaction for expired session order {cashfree_order_id} with status {payment_transaction.status}")
            
            if payment_transaction.status == 'SUCCESS':
                # Check if tickets exist for this transaction
                recent_tickets = Ticket.objects.filter(
                    purchase_transaction=payment_transaction
                ).select_related('event', 'ticket_type')
                
                if recent_tickets.exists():
                    # Tickets already exist, show success page
                    messages.info(request, "Your payment was already processed successfully.")
                    return render(request, 'core/payment_success.html', {
                        'order_id': cashfree_order_id,
                        'transaction_id': payment_transaction.transaction_id,
                        'recent_tickets': recent_tickets,
                    })
                else:
                    # Payment successful but no tickets created - recover ticket_order from transaction data
                    response_data = payment_transaction.response_data or {}
                    ticket_order = response_data.get('ticket_order', {})
                    
                    if ticket_order:
                        logger.info(f"Recovered ticket_order from transaction data for {cashfree_order_id}")
                        # Continue with normal ticket creation process below
                    else:
                        messages.error(request, "Your session has expired and we cannot recover your order details. Please contact support with your order ID.")
                        return redirect('home')
            else:
                messages.error(request, "Your payment status is not successful. Please contact support.")
                return redirect('home')
        except PaymentTransaction.DoesNotExist:
            messages.error(request, "Your session has expired. Please contact support if payment was deducted.")
            return redirect('home')

    # Get or create the payment transaction record
    payment_transaction = None
    try:
        payment_transaction = PaymentTransaction.objects.get(order_id=cashfree_order_id)
        logger.info(f"Found existing transaction record for order {cashfree_order_id}, status: {payment_transaction.status}")

        # If payment was already successfully processed, don't process again
        if payment_transaction.status == 'SUCCESS':
            logger.info(f"Transaction {cashfree_order_id} was already marked as successful, showing success page")
            messages.info(request, "Your payment was already processed successfully.")

            # Get the tickets that were created for this transaction
            recent_tickets = Ticket.objects.filter(
                purchase_transaction=payment_transaction
            ).select_related('event', 'ticket_type')
            
            # Fix any tickets with missing unique_id
            for ticket in recent_tickets:
                if not ticket.unique_id:
                    ticket.unique_id = uuid_module.uuid4()
                    if not ticket.unique_secure_token:
                        ticket.unique_secure_token = str(uuid_module.uuid4())
                    ticket.save()
                    logger.info(f"Fixed missing unique_id for ticket {ticket.id} from transaction {cashfree_order_id}")

            return render(request, 'core/payment_success.html', {
                'order_id': cashfree_order_id,
                'transaction_id': payment_transaction.transaction_id,
                'recent_tickets': recent_tickets,
            })
    except PaymentTransaction.DoesNotExist:
        logger.info(f"No transaction record found for order {cashfree_order_id}, creating new record")
        # Set payment gateway to 'SANDBOX' if in debug mode to distinguish test transactions
        gateway_type = 'SANDBOX' if settings.DEBUG else 'Cashfree'
        payment_transaction = PaymentTransaction.objects.create(
            user=request.user,
            order_id=cashfree_order_id,
            transaction_id=transaction_id,
            amount=float(ticket_order.get('total', 0)),
            status='PENDING',
            payment_gateway=gateway_type,
            response_data={
                'initial_callback_params': dict(request.GET.items()),
                'environment': 'SANDBOX' if settings.DEBUG else 'PRODUCTION'
            }
        )

    try:
        # Verify payment status with Cashfree servers
        order_details = None
        # Use the same API version as used during order creation to avoid schema mismatch
        # (module-level constant set above)

        # Enhanced payment verification using multiple sources
        api_order_status = None
        api_payment_status = None

        # Step 1: Try to verify using Cashfree API (most reliable source)
        try:
            logger.info(f"Verifying payment status via Cashfree API for order {cashfree_order_id}")
            # Extra validation
            if not cashfree_order_id or not isinstance(cashfree_order_id, str) or not cashfree_order_id.startswith("order_"):
                logger.error(f"Invalid cashfree_order_id: {cashfree_order_id} (type: {type(cashfree_order_id)})")
                raise ValueError("Invalid order_id for Cashfree API")
            
            # Validate credentials before making API calls
            if not settings.CASHFREE_CLIENT_ID or not settings.CASHFREE_CLIENT_SECRET:
                logger.error("Missing Cashfree credentials")
                raise ValueError("Cashfree credentials not configured")
            
            # Use direct HTTP request to avoid SDK header issues
            import requests
            
            # Set up API endpoint based on environment
            if settings.DEBUG:
                base_url = "https://sandbox.cashfree.com/pg"
                logger.info("Using SANDBOX environment for payment verification")
            else:
                base_url = "https://api.cashfree.com/pg"
                logger.info("Using PRODUCTION environment for payment verification")
            
            endpoint = f"{base_url}/orders/{cashfree_order_id}"
            
            headers = {
                "Accept": "application/json",
                "x-api-version": str(CASHFREE_API_VERSION),
                "x-client-id": str(settings.CASHFREE_CLIENT_ID),
                "x-client-secret": str(settings.CASHFREE_CLIENT_SECRET)
            }
            
            response = requests.get(endpoint, headers=headers, timeout=30)
            
            if response.status_code == 200:
                order_data = response.json()
                
                # Extract payment details from API response
                api_order_status = order_data.get('order_status', '').upper()
                api_payment_status = ''  # Not always available in order details
                api_transaction_id = order_data.get('transaction_id')
                cf_order_id = order_data.get('cf_order_id')
                
                logger.info(f"API verification successful - Order status: {api_order_status}, CF Order ID: {cf_order_id}")
                
                # Create a fake order_details object to match the existing logic below
                class MockOrderData:
                    def __init__(self, data):
                        self.order_status = data.get('order_status', '')
                        self.payment_status = api_payment_status  # May be empty
                        self.transaction_id = data.get('transaction_id')
                        self.cf_order_id = data.get('cf_order_id')
                        
                class MockOrderDetails:
                    def __init__(self, data):
                        self.data = MockOrderData(data)
                        
                order_details = MockOrderDetails(order_data)
                
                # Store response data for auditing
                payment_transaction.response_data = {
                    **(payment_transaction.response_data or {}),
                    'api_response': {
                        'order_status': api_order_status,
                        'payment_status': api_payment_status,
                        'transaction_id': api_transaction_id,
                        'cf_order_id': cf_order_id,
                        'verification_timestamp': timezone.now().isoformat(),
                        'raw_response': order_data
                    }
                }
                payment_transaction.save()
                
                # Update transaction ID if available from API
                if api_transaction_id:
                    payment_transaction.transaction_id = api_transaction_id
                    
            else:
                logger.error(f"Cashfree API returned {response.status_code}: {response.text}")
                raise Exception(f"API returned {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"Error verifying payment with Cashfree API: {e}")
            payment_transaction.response_data = {
                **(payment_transaction.response_data or {}),
                'api_error': str(e),
                'api_error_timestamp': timezone.now().isoformat(),
            }
            payment_transaction.save()

        # Store response data for auditing
        if order_details and hasattr(order_details, 'data'):
            api_order_status = getattr(order_details.data, 'order_status', '').upper()
            api_payment_status = getattr(order_details.data, 'payment_status', '').upper()
            api_transaction_id = getattr(order_details.data, 'transaction_id', None)

            # Update transaction ID if available from API
            if api_transaction_id:
                payment_transaction.transaction_id = api_transaction_id

            payment_transaction.response_data = {
                **(payment_transaction.response_data or {}),
                'api_response': {
                    'order_status': api_order_status,
                    'payment_status': api_payment_status,
                    'transaction_id': api_transaction_id,
                    'verification_timestamp': timezone.now().isoformat(),
                }
            }
            payment_transaction.save()

            logger.info(f"API verification result - Order status: {api_order_status}, Payment status: {api_payment_status}")

        # Step 2: Payment verification logic with multiple checks
        payment_verified = False
        verification_source = None

        # Check API response first (most reliable)
        if api_order_status or api_payment_status:
            # Success indicators from API
            if api_order_status in ["PAID", "SUCCESS"] or api_payment_status in ["SUCCESS", "CAPTURED"]:
                payment_verified = True
                verification_source = "api"
                logger.info(f"Payment verified as successful via API response for order {cashfree_order_id}")
            # Clear failure indicators from API
            elif api_order_status in ["FAILED", "CANCELLED"] or api_payment_status in ["FAILED", "CANCELLED"]:
                payment_verified = False
                verification_source = "api"
                logger.warning(f"Payment explicitly failed/cancelled according to API for order {cashfree_order_id}")

        # If API verification didn't provide a clear answer, fall back to callback parameters
        if verification_source is None:
            logger.warning(f"Using fallback (callback parameters) for payment verification of order {cashfree_order_id}")
            if payment_status_param == "SUCCESS":
                payment_verified = True
                verification_source = "callback"
                logger.info(f"Payment verified as successful via callback parameters for order {cashfree_order_id}")
            elif payment_status_param in ["FAILED", "CANCELLED"]:
                payment_verified = False
                verification_source = "callback"
                logger.warning(f"Payment explicitly failed/cancelled according to callback params for order {cashfree_order_id}")
            else:
                # If callback doesn't explicitly say failed, keep it undecided; don't mark failed by default
                logger.info("Callback did not include definitive payment status; awaiting reliable source")

        # Step 3: Update payment transaction with verification result
        payment_transaction.response_data = {
            **(payment_transaction.response_data or {}),
            'payment_verified': payment_verified,
            'verification_source': verification_source,
            'verification_timestamp': timezone.now().isoformat(),
        }
        payment_transaction.save()

        # Step 4: Handle failed/cancelled/unknown payments
        if not payment_verified:
            # If we couldn't verify via API and callback didn't provide a definitive status,
            # don't mark as failed; keep it pending and show a processing page.
            if verification_source is None:
                payment_transaction.status = 'PENDING'
                payment_transaction.save()
                messages.info(request, "We're processing your payment. This can take a few seconds. If this page doesn't update automatically, please refresh after 10–20 seconds. If money was deducted but the status doesn't change, contact support with your Order ID.")
                context = {
                    'order_id': cashfree_order_id,
                    'event_id': ticket_order['event_id'],
                    'failure_reason': 'PENDING'
                }
                return render(request, 'core/payment_failed.html', context)

            # Update payment status based on specific failure reason if available
            if payment_status_param == 'CANCELLED' or api_order_status == 'CANCELLED' or api_payment_status == 'CANCELLED':
                payment_transaction.status = 'CANCELLED'
                failure_message = "Payment was cancelled. No tickets have been booked."
            else:
                payment_transaction.status = 'FAILED'
                failure_message = "Payment was not completed successfully. No tickets have been booked."

            payment_transaction.save()

            messages.error(request, failure_message)
            logger.warning(f"Payment failed/cancelled for order {cashfree_order_id} - Status set to {payment_transaction.status}")

            # Clean up the session but keep the ticket order so user can try again
            if session_order_id in request.session:
                del request.session[session_order_id]

            # Render payment failed page
            # Determine the failure reason from the appropriate source
            if verification_source == "api":
                failure_reason = api_order_status or api_payment_status or "UNKNOWN"
            else:
                failure_reason = payment_status_param or "UNKNOWN"
                
            context = {
                'order_id': cashfree_order_id,
                'event_id': ticket_order['event_id'],
                'failure_reason': failure_reason
            }
            return render(request, 'core/payment_failed.html', context)
        
        # Step 5: Process successful payment and create tickets
        with transaction.atomic():
            # Update payment status first
            payment_transaction.status = 'SUCCESS'
            if transaction_id and not payment_transaction.transaction_id:
                payment_transaction.transaction_id = transaction_id
            payment_transaction.save()
            
            logger.info(f"Payment marked as successful for order {cashfree_order_id}")
            
            # Check if tickets were already created for this transaction to avoid duplicates
            existing_tickets = Ticket.objects.filter(
                purchase_transaction_id=payment_transaction.id
            )
            
            # Get event for promo code processing
            event_id = ticket_order['event_id']
            event = get_object_or_404(Event, id=event_id)
            
            if existing_tickets.exists():
                logger.info(f"{existing_tickets.count()} tickets already created for transaction {payment_transaction.id}, skipping creation")
                recent_tickets = existing_tickets.select_related('event', 'ticket_type')
            else:
                logger.info(f"Creating new tickets for verified payment {cashfree_order_id}")
                selected_tickets = ticket_order.get('ticket_types', [])
                
                created_tickets = []
                for ticket_data in selected_tickets:
                    ticket_type = get_object_or_404(TicketType, id=ticket_data['id'])
                    
                    # Calculate consolidated ticket details
                    attendees_per_ticket = ticket_type.attendees_per_ticket or 1
                    booking_quantity = ticket_data['quantity']
                    total_admissions = booking_quantity * attendees_per_ticket
                    
                    # Create single consolidated ticket instead of multiple tickets
                    ticket = Ticket.objects.create(
                        event=event,
                        ticket_type=ticket_type,
                        customer=request.user,
                        ticket_number=generate_ticket_number(),
                        status='SOLD',
                        purchase_date=timezone.now(),
                        unique_secure_token=str(uuid_module.uuid4()),
                        unique_id=uuid_module.uuid4(),  # Ensure unique_id is set for email URLs
                        purchase_transaction=payment_transaction,  # Link ticket to transaction
                        booking_quantity=booking_quantity,
                        total_admission_count=total_admissions
                    )
                    created_tickets.append(ticket)

                # Update payment transaction with ticket information
                payment_transaction.response_data = {
                    **(payment_transaction.response_data or {}),
                    'tickets_created': [t.id for t in created_tickets],
                    'ticket_count': len(created_tickets),
                    'ticket_creation_timestamp': timezone.now().isoformat()
                }
                payment_transaction.save()
                
                # Store tickets for display
                recent_tickets = Ticket.objects.filter(id__in=[t.id for t in created_tickets]).select_related('event', 'ticket_type')

            # Handle promo code if used (moved outside ticket creation to ensure it always runs)
            promo_code_str = ticket_order.get('promo_code')
            if promo_code_str:
                try:
                    # Check if promo code usage already exists for this transaction to avoid duplicates
                    existing_usage = PromoCodeUsage.objects.filter(
                        promo_code__code=promo_code_str,
                        user=request.user,
                        ticket__purchase_transaction=payment_transaction
                    ).first()
                    
                    if not existing_usage:
                        promo_code = PromoCode.objects.get(code=promo_code_str, event=event)
                        # Only increment current_uses after successful payment verification
                        # This ensures promo code analytics only reflect actual successful purchases
                        promo_code.current_uses += 1
                        promo_code.save()
                        
                        PromoCodeUsage.objects.create(
                            promo_code=promo_code,
                            user=request.user,
                            ticket=recent_tickets.first() if recent_tickets else None,
                            order_total=ticket_order.get('subtotal', 0),
                            discount_amount=ticket_order.get('discount', 0)
                        )
                        
                        logger.info(f"Promo code {promo_code_str} applied successfully for order {cashfree_order_id}")
                    else:
                        logger.info(f"Promo code usage already recorded for order {cashfree_order_id}")
                except Exception as e:
                    logger.error(f"Error processing promo code: {str(e)}")
                    # Don't fail the whole transaction if promo code processing fails

        # Generate invoices for each ticket
        from .invoice_utils import create_invoice_for_ticket, send_invoice_email
        
        invoices_generated = 0
        tickets_emailed = 0
        
        for ticket in recent_tickets:
            try:
                # Create invoice record
                invoice = create_invoice_for_ticket(ticket, payment_transaction)
                
                if invoice:
                    # Send invoice email with PDF attachment
                    email_sent = send_invoice_email(invoice)
                    
                    if email_sent:
                        invoices_generated += 1
                        logger.info(f"Invoice #{invoice.invoice_number} generated and sent for ticket {ticket.ticket_number}")
                    else:
                        logger.error(f"Failed to send invoice email for ticket {ticket.ticket_number}")
                        
            except Exception as e:
                logger.error(f"Error generating invoice for ticket {ticket.ticket_number}: {str(e)}")
                logger.error(traceback_module.format_exc())
            
            # Send ticket confirmation email with online pass link
            try:
                ticket_email_sent = send_ticket_confirmation_email(ticket, request)
                if ticket_email_sent:
                    tickets_emailed += 1
                    logger.info(f"Ticket confirmation email sent for ticket {ticket.ticket_number}")
                else:
                    logger.error(f"Failed to send ticket confirmation email for ticket {ticket.ticket_number}")
            except Exception as e:
                logger.error(f"Error sending ticket confirmation email for ticket {ticket.ticket_number}: {str(e)}")
                logger.error(traceback_module.format_exc())
        
        # Clean up the session
        if session_order_id in request.session:
            del request.session[session_order_id]
        if 'ticket_order' in request.session:
            del request.session['ticket_order']
        
        logger.info(f"Successfully processed payment, created {recent_tickets.count()} tickets, sent {invoices_generated} invoices, and sent {tickets_emailed} ticket confirmation emails for order {cashfree_order_id}")
        messages.success(request, "Payment successful and tickets booked! Check your email for ticket confirmation and invoice. You can also view them in 'My Tickets'.")

    except Exception as e:
        # Update payment status to failed
        if payment_transaction:
            payment_transaction.status = 'FAILED'
            payment_transaction.response_data = {
                **(payment_transaction.response_data or {}),
                'processing_error': str(e)
            }
            payment_transaction.save()
            
        logger.error(f"Error creating tickets after payment for order {cashfree_order_id}: {e}")
        logger.error(traceback_module.format_exc())  # Log the full stack trace
        messages.error(request, "There was an error processing your order. Please contact support with your order ID.")
        
        # Render payment failed page with error context
        context = {
            'order_id': cashfree_order_id,
            'event_id': ticket_order.get('event_id'),
            'error_message': "There was a technical error processing your payment. Please contact support."
        }
        return render(request, 'core/payment_failed.html', context)

    # Prepare success context with tickets
    context = {
        'order_id': cashfree_order_id,
        'transaction_id': payment_transaction.transaction_id,
        'recent_tickets': recent_tickets,
    }
    return render(request, 'core/payment_success.html', context)

def get_payment_gateway_response(event_id):
    # Simulate payment gateway response
    # Replace this with actual API call to the payment gateway
    return {
        'status': 'SUCCESS',  # or 'FAILED'
        'failure_reason': None  # Provide reason if failed
    }

# --- CASHFREE WEBHOOK SIGNATURE VERIFICATION ---
def verify_cashfree_signature(payload, signature, timestamp):
    """
    Verifies the webhook signature received from Cashfree to ensure authenticity.
    Uses the API Secret (Client Secret) as per Cashfree's webhook verification process.
    """
    if not signature or not timestamp:
        logger.warning("Webhook signature verification failed: Missing signature or timestamp")
        return False
    
    # Use the API Secret (Client Secret) for webhook verification as per Cashfree documentation
    secret_key = getattr(settings, 'CASHFREE_CLIENT_SECRET', None)
    if not secret_key:
        logger.error("Webhook signature verification failed: CASHFREE_CLIENT_SECRET not configured")
        return False
    
    # Cashfree webhook signature format: HMAC SHA-256 of (timestamp + payload) using API Secret
    message = timestamp + payload
    secret_bytes = secret_key.encode('utf-8')
    message_bytes = message.encode('utf-8')
    hash_obj = hmac.new(secret_bytes, msg=message_bytes, digestmod=hashlib.sha256)
    expected_signature = base64.b64encode(hash_obj.digest()).decode('utf-8')
    
    is_valid = hmac.compare_digest(expected_signature, signature)
    if not is_valid:
        logger.warning(f"Webhook signature verification failed: Expected {expected_signature}, got {signature}")
        logger.info(f"Payload: {payload[:100]}... (truncated)")
        logger.info(f"Timestamp: {timestamp}")
    
    return is_valid

# --- TICKET CREATION FOR PAYMENTTRANSACTION ---
def create_tickets_for_payment(transaction):
    """
    Create tickets for a successful PaymentTransaction.
    This function is idempotent: it will not create duplicate tickets if already created.
    """
    from .models import Ticket, Event
    from django.db import transaction as db_transaction
    
    if transaction.status != 'SUCCESS':
        raise ValueError('Transaction must be marked as SUCCESS before creating tickets.')
    
    # Check if tickets already exist for this transaction
    existing_tickets = Ticket.objects.filter(purchase_transaction=transaction)
    if existing_tickets.exists():
        return list(existing_tickets)
    
    # Get ticket order data from response_data
    ticket_order = transaction.response_data.get('ticket_order', {})
    if not ticket_order:
        raise ValueError('No ticket order data found in transaction response_data.')
    
    event_id = ticket_order.get('event_id')
    ticket_types = ticket_order.get('ticket_types', {})
    # Fix: handle ticket_types as list or dict
    if isinstance(ticket_types, list):
        # Convert list of dicts like [{'id': 5, 'quantity': 2}, ...] to {5: 2, ...}
        try:
            ticket_types_dict = {}
            for entry in ticket_types:
                if isinstance(entry, dict) and 'id' in entry and 'quantity' in entry:
                    ticket_types_dict[entry['id']] = entry['quantity']
            ticket_types = ticket_types_dict
        except Exception as e:
            logger.error(f"ticket_types is a list but could not convert to dict: {e}")
            ticket_types = {}
    elif not isinstance(ticket_types, dict):
        logger.error(f"ticket_types is not a dict or list: {type(ticket_types)}")
        ticket_types = {}
    total_attendees = ticket_order.get('total_attendees', 1)
    
    if not event_id:
        raise ValueError('No event_id found in ticket order data.')
    
    # Get the event
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        raise ValueError(f'Event with id {event_id} does not exist.')
    
    # Check event capacity
    with db_transaction.atomic():
        event.refresh_from_db()
        if hasattr(event, 'remaining_attendee_capacity'):
            remaining = event.remaining_attendee_capacity
        else:
            # Fallback: calculate manually
            sold = Ticket.objects.filter(event=event, status__in=['SOLD', 'VALID']).count()
            remaining = max(0, event.capacity - sold)
        
        if total_attendees > remaining:
            transaction.payment_status = 'Error - Capacity'
            transaction.save()
            raise ValueError(f'Not enough event capacity to create tickets. Need {total_attendees}, available {remaining}.')
        
        # Create tickets based on ticket types
        tickets = []
        for ticket_type_id, quantity in ticket_types.items():
            if quantity > 0:
                try:
                    ticket_type = event.ticket_types.get(id=ticket_type_id)
                    
                    # Calculate consolidated ticket details
                    attendees_per_ticket = ticket_type.attendees_per_ticket or 1
                    booking_quantity = quantity
                    total_admissions = booking_quantity * attendees_per_ticket
                    
                    # Create single consolidated ticket instead of multiple tickets
                    ticket_code = str(uuid_module.uuid4())[:10].upper()
                    ticket = Ticket.objects.create(
                        purchase_transaction=transaction,
                        event=event,
                        ticket_type=ticket_type,
                        customer=transaction.user,
                        ticket_number=ticket_code,
                        status='SOLD',
                        purchase_date=timezone.now(),
                        unique_id=uuid_module.uuid4(),  # Ensure unique_id is set for email URLs
                        unique_secure_token=str(uuid_module.uuid4()),  # Also set secure token
                        booking_quantity=booking_quantity,
                        total_admission_count=total_admissions
                    )
                    tickets.append(ticket)
                except Exception as e:
                    logger.error(f"Error creating ticket for type {ticket_type_id}: {str(e)}")
                    raise
        
        # Update event tickets_sold if present
        if hasattr(event, 'tickets_sold'):
            event.tickets_sold = event.tickets_sold + total_attendees
            event.save()
        
        logger.info(f"Created {len(tickets)} tickets for transaction {transaction.order_id}")
        
        # Handle promo code if used
        promo_code_str = ticket_order.get('promo_code')
        if promo_code_str and tickets:
            try:
                # Check if promo code usage already exists for this transaction to avoid duplicates
                existing_usage = PromoCodeUsage.objects.filter(
                    promo_code__code=promo_code_str,
                    user=transaction.user,
                    ticket__purchase_transaction=transaction
                ).first()
                
                if not existing_usage:
                    promo_code = PromoCode.objects.get(code=promo_code_str, event=event)
                    # Only increment current_uses for successful transactions
                    # This ensures promo code analytics only reflect actual successful purchases
                    promo_code.current_uses += 1
                    promo_code.save()
                    
                    PromoCodeUsage.objects.create(
                        promo_code=promo_code,
                        user=transaction.user,
                        ticket=tickets[0],  # Link to first ticket
                        order_total=ticket_order.get('subtotal', 0),
                        discount_amount=ticket_order.get('discount', 0)
                    )
                    
                    logger.info(f"Promo code {promo_code_str} applied successfully for transaction {transaction.order_id}")
                else:
                    logger.info(f"Promo code usage already recorded for transaction {transaction.order_id}")
            except PromoCode.DoesNotExist:
                logger.error(f"Promo code {promo_code_str} does not exist for event {event.id}")
            except Exception as e:
                logger.error(f"Error processing promo code: {str(e)}")
                # Don't fail the whole transaction if promo code processing fails
        
        # Send emails for all created tickets
        from django.test import RequestFactory
        from .invoice_utils import create_invoice_for_ticket, send_invoice_email
        
        factory = RequestFactory()
        request = factory.get('/')
        request.user = transaction.user
        
        invoices_generated = 0
        tickets_emailed = 0
        
        for ticket in tickets:
            try:
                # Send invoice email
                invoice = create_invoice_for_ticket(ticket, transaction)
                if invoice:
                    if send_invoice_email(invoice):
                        invoices_generated += 1
                        logger.info(f"Invoice email sent for ticket {ticket.ticket_number}")
                    else:
                        logger.error(f"Failed to send invoice email for ticket {ticket.ticket_number}")
                else:
                    logger.error(f"Failed to create invoice for ticket {ticket.ticket_number}")
            except Exception as e:
                logger.error(f"Error sending invoice email for ticket {ticket.ticket_number}: {str(e)}")
                
            try:
                # Send ticket confirmation email
                if send_ticket_confirmation_email(ticket, request):
                    tickets_emailed += 1
                    logger.info(f"Ticket confirmation email sent for ticket {ticket.ticket_number}")
                else:
                    logger.error(f"Failed to send ticket confirmation email for ticket {ticket.ticket_number}")
            except Exception as e:
                logger.error(f"Error sending ticket confirmation email for ticket {ticket.ticket_number}: {str(e)}")
        
        logger.info(f"Email summary for transaction {transaction.order_id}: {invoices_generated} invoices sent, {tickets_emailed} ticket confirmations sent")
        
        return tickets

# --- CASHFREE WEBHOOK HANDLER ---
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def cashfree_webhook(request):
    """
    Handles incoming webhook notifications from Cashfree Payments for PaymentTransaction.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)
    raw_payload = request.body.decode('utf-8')
    signature = request.headers.get('x-webhook-signature')
    timestamp = request.headers.get('x-webhook-timestamp')
    if not verify_cashfree_signature(raw_payload, signature, timestamp):
        return HttpResponse(status=401)
    try:
        data = json.loads(raw_payload)
        payment_data = data.get('data', {}).get('payment', {})
        order_data = data.get('data', {}).get('order', {})
        payment_status = payment_data.get('payment_status')
        order_id = order_data.get('order_id')
        cf_payment_id = payment_data.get('cf_payment_id')
        # Find the PaymentTransaction by order_id
        from .models import PaymentTransaction
        try:
            transaction = PaymentTransaction.objects.get(order_id=order_id)
        except PaymentTransaction.DoesNotExist:
            return HttpResponse(status=404)
        # Prevent duplicate processing
        if transaction.status == 'SUCCESS':
            return HttpResponse(status=200)
        
        if payment_status == 'SUCCESS':
            transaction.status = 'SUCCESS'
            transaction.payment_status = 'Paid'
            transaction.cf_payment_id = cf_payment_id
            transaction.save()
            try:
                tickets = create_tickets_for_payment(transaction)
                logger.info(f"Successfully created {len(tickets)} tickets for transaction {order_id}")
                
                # Verify all tickets have unique_id set
                for ticket in tickets:
                    if not ticket.unique_id or not ticket.unique_secure_token:
                        if not ticket.unique_id:
                            ticket.unique_id = uuid_module.uuid4()
                        if not ticket.unique_secure_token:
                            ticket.unique_secure_token = str(uuid_module.uuid4())
                        ticket.save()
                        logger.info(f"Fixed missing unique_id or unique_secure_token for ticket {ticket.id} from transaction {order_id}")
            except Exception as e:
                logger.error(f"Error creating tickets for transaction {order_id}: {str(e)}")
                # Continue processing - don't fail the webhook
        elif payment_status in ['FAILED', 'USER_DROPPED', 'CANCELLED']:
            transaction.status = 'FAILED'
            transaction.payment_status = 'Failed'
            transaction.save()
        # Always acknowledge receipt
        return HttpResponse(status=200)
    except Exception as e:
        logger.error(f"Error processing webhook for order {order_id}: {str(e)}")
        return HttpResponse(status=400)

def payment_failed(request):
    return render(request, 'core/payment_failed.html')

# New view for the event-specific organizer dashboard
@login_required
@user_passes_test(is_organizer)
def event_dashboard(request, event_id):
    event = get_object_or_404(Event, id=event_id, organizer=request.user)
    
    # Calculate total revenue
    sold_tickets = Ticket.objects.filter(event=event, status='SOLD').select_related('ticket_type')
    total_revenue = sum(ticket.ticket_type.price for ticket in sold_tickets)
    
    # Calculate tickets sold and remaining
    tickets_sold = sold_tickets.count()
    tickets_remaining = event.capacity - tickets_sold
    
    # Get ticket sales over time (for the line chart)
    # Group by date and count
    sales_by_date = {}
    tickets_by_type = {}
    
    # Initialize ticket types
    for ticket_type in event.ticket_types.all():
        tickets_by_type[ticket_type.id] = {
            'name': ticket_type.type_name,
            'count': 0,
            'revenue': 0
        }
    
    # Process ticket data for charts
    for ticket in sold_tickets:
        # For sales over time
        purchase_date = ticket.purchase_date.date() if ticket.purchase_date else timezone.now().date()
        date_str = purchase_date.strftime('%Y-%m-%d')
        if date_str not in sales_by_date:
            sales_by_date[date_str] = 0
        sales_by_date[date_str] += 1
        
        # For ticket type breakdown
        if ticket.ticket_type and ticket.ticket_type.id in tickets_by_type:
            tickets_by_type[ticket.ticket_type.id]['count'] += 1
            tickets_by_type[ticket.ticket_type.id]['revenue'] += float(ticket.ticket_type.price)
    
    # Convert to sorted lists for charts
    sales_dates = sorted(sales_by_date.keys())
    sales_counts = [sales_by_date[date] for date in sales_dates]
    
    # Format dates for display
    formatted_dates = []
    for date_str in sales_dates:
        try:
            date_obj = dt.strptime(date_str, '%Y-%m-%d')
            formatted_dates.append(date_obj.strftime('%b %d'))
        except ValueError:
            # In case of invalid date string, use a placeholder
            formatted_dates.append('Unknown')
    
    # Format ticket type data for pie chart
    ticket_types_data = list(tickets_by_type.values())
    
    context = {
        'event': event,
        'total_revenue': total_revenue,
        'tickets_sold': tickets_sold,
        'tickets_remaining': tickets_remaining,
        'sales_dates': formatted_dates,
        'sales_counts': sales_counts,
        'ticket_types_data': ticket_types_data,
    }
    
    return render(request, 'core/event_dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.role == 'ORGANIZER')
def download_organizer_report(request):
    """Download a comprehensive report of all events and ticket sales for an organizer in various formats"""
    format_type = request.GET.get('format', 'csv')
    
    # Get all events for this organizer
    events = Event.objects.filter(organizer=request.user)
    
    # Check if there's any data to report
    has_data = False
    for event in events:
        tickets = Ticket.objects.filter(event=event).exists()
        if tickets:
            has_data = True
            break
    
    if not has_data:
        messages.warning(request, "No ticket data available to download.")
        return redirect('dashboard')
    
    if format_type == 'pdf':
        import datetime as dt  # Use dt as alias to avoid conflict
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib.units import inch
        
        # Create a response object for PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="organizer_report_{dt.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        
        # Create the PDF document using ReportLab
        doc = SimpleDocTemplate(response, pagesize=landscape(letter))
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Add a title
        elements.append(Paragraph("Event & Ticket Sales Report", title_style))
        elements.append(Paragraph(f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
        elements.append(Paragraph(f"Organizer: {request.user.first_name} {request.user.last_name}", subtitle_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Process each event
        for event in events:
            # Add event details
            elements.append(Paragraph(f"Event: {event.title}", subtitle_style))
            elements.append(Paragraph(f"Date: {event.date.strftime('%Y-%m-%d')}", normal_style))
            elements.append(Paragraph(f"Venue: {event.venue}", normal_style))
            elements.append(Spacer(1, 0.1*inch))
            
            # Get ticket data for this event
            tickets = Ticket.objects.filter(
                event=event
            ).select_related('ticket_type', 'customer', 'validated_by')
            
            if tickets:
                # Create data for table
                data = [['Ticket Type', 'Ticket Number', 'Customer', 'Email', 'Purchase Date', 'Price', 'Status', 'Check-in']]
                
                for ticket in tickets:
                    customer_name = f"{ticket.customer.first_name} {ticket.customer.last_name}" if ticket.customer else 'N/A'
                    data.append([
                        ticket.ticket_type.type_name if ticket.ticket_type else 'N/A',
                        ticket.ticket_number,
                        customer_name,
                        ticket.customer.email if ticket.customer else 'N/A',
                        ticket.purchase_date.strftime("%Y-%m-%d %H:%M") if ticket.purchase_date else 'N/A',
                        f"₹{ticket.ticket_type.price}" if ticket.ticket_type else 'N/A',
                        ticket.status,
                        ticket.used_at.strftime("%Y-%m-%d %H:%M") if ticket.used_at else 'Not checked in'
                    ])
                
                # Create table with data
                ticket_table = Table(data)
                ticket_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(ticket_table)
                
                # Add summary statistics
                total_sold = tickets.filter(status='SOLD').count()
                total_checked_in = tickets.filter(status='USED').count()
                total_revenue = sum(ticket.ticket_type.price for ticket in tickets if ticket.ticket_type)
                
                elements.append(Spacer(1, 0.2*inch))
                elements.append(Paragraph(f"Total Tickets Sold: {total_sold}", normal_style))
                elements.append(Paragraph(f"Total Check-ins: {total_checked_in}", normal_style))
                elements.append(Paragraph(f"Total Revenue: ₹{total_revenue}", normal_style))
            else:
                elements.append(Paragraph("No tickets sold for this event yet.", normal_style))
            
            elements.append(Spacer(1, 0.5*inch))
        
        # Build the PDF
        doc.build(elements)
        return response
        
    else:  # Default to CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="organizer_report_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Event Title', 'Event Date', 'Ticket Type', 'Ticket Number', 
            'Customer Email', 'Customer Name', 'Purchase Date', 'Price', 
            'Status', 'Check-in Time', 'Attendees'
        ])
        
        # For each event, get all tickets
        for event in events:
            tickets = Ticket.objects.filter(
                event=event
            ).select_related('ticket_type', 'customer', 'validated_by')
            
            for ticket in tickets:
                # Calculate number of attendees for this ticket
                attendees = ticket.ticket_type.attendees_per_ticket if ticket.ticket_type and ticket.ticket_type.attendees_per_ticket else 1
                
                writer.writerow([
                    event.title,
                    event.date.strftime("%Y-%m-%d"),
                    ticket.ticket_type.type_name if ticket.ticket_type else 'N/A',
                    ticket.ticket_number,
                    ticket.customer.email if ticket.customer else 'N/A',
                    f"{ticket.customer.first_name} {ticket.customer.last_name}" if ticket.customer else 'N/A',
                    ticket.purchase_date.strftime("%Y-%m-%d %H:%M") if ticket.purchase_date else 'N/A',
                    ticket.ticket_type.price if ticket.ticket_type else 'N/A',
                    ticket.status,
                    ticket.used_at.strftime("%Y-%m-%d %H:%M") if ticket.used_at else 'N/A',
                    attendees
                ])
        
        return response
        
@login_required
@user_passes_test(lambda u: u.role == 'ORGANIZER')
def download_ticket_sales(request):
    """Download detailed CSV of all ticket sales for an organizer's events"""
    import datetime as dt  # Use dt as alias to avoid conflict
    
    # Get all events for this organizer
    events = Event.objects.filter(organizer=request.user)
    
    # Check if there's any data to report
    has_data = False
    for event in events:
        tickets = Ticket.objects.filter(event=event, status__in=['SOLD', 'USED']).exists()
        if tickets:
            has_data = True
            break
    
    if not has_data:
        messages.warning(request, "No ticket sales data available to download.")
        return redirect('dashboard')
    
    response = HttpResponse(content_type='text/csv')
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    response['Content-Disposition'] = f'attachment; filename="ticket_sales_{timestamp}.csv"'
    
    writer = csv.writer(response)
    
    # Write header with more detailed ticket information
    writer.writerow([
        'Event Title', 
        'Event Date', 
        'Ticket Type', 
        'Ticket Number', 
        'Price', 
        'Customer Email', 
        'Customer Name',
        'Customer Phone',
        'Purchase Date', 
        'Payment Status',
        'Check-in Status',
        'Check-in Time', 
        'Checked-in By',
        'Promo Code Used',
        'Discount Amount'
    ])
    
    # Get all events for this organizer
    events = Event.objects.filter(organizer=request.user)
    
    # For each event, get all sold tickets
    for event in events:
        tickets = Ticket.objects.filter(
            event=event,
            status__in=['SOLD', 'USED']  # Only include sold or used tickets
        ).select_related('ticket_type', 'customer', 'validated_by')
        
        for ticket in tickets:
            # Get promo code information if available
            promo_code_usage = PromoCodeUsage.objects.filter(ticket=ticket).first()
            promo_code = promo_code_usage.promo_code.code if promo_code_usage else 'None'
            discount_amount = promo_code_usage.discount_amount if promo_code_usage else 0
            
            writer.writerow([
                event.title,
                event.date.strftime("%Y-%m-%d"),
                ticket.ticket_type.type_name if ticket.ticket_type else 'N/A',
                ticket.ticket_number,
                ticket.ticket_type.price if ticket.ticket_type else 'N/A',
                ticket.customer.email if ticket.customer else 'N/A',
                f"{ticket.customer.first_name} {ticket.customer.last_name}" if ticket.customer else 'N/A',
                ticket.customer.mobile_number if ticket.customer else 'N/A',
                ticket.purchase_date.strftime("%Y-%m-%d %H:%M") if ticket.purchase_date else 'N/A',
                'Paid' if ticket.status in ['SOLD', 'USED'] else 'Not Paid',
                'Checked In' if ticket.status == 'USED' else 'Not Checked In',
                ticket.used_at.strftime("%Y-%m-%d %H:%M") if ticket.used_at else 'N/A',
                f"{ticket.validated_by.first_name} {ticket.validated_by.last_name}" if ticket.validated_by else 'N/A',
                promo_code,
                discount_amount
            ])
    
    return response


def test_static_files(request):
    """
    Test view to verify static files are working correctly
    """
    import os
    from pathlib import Path
    
    # Check if static files exist
    static_root = Path(settings.STATIC_ROOT)
    static_files_status = {}
    
    # Check key static files
    key_files = [
        'core/images/TAPNEX_LOGO_BG.jpg',
        'core/images/LOGO_NEXGEN_FC.png',
        'sounds/SUCCESSFUL_SCAN.mp3',
        'sounds/FAILED_NOT VALIDATED.wav',
        'core/css/styles.css',
        'css/event_pass.css'
    ]
    
    for file_path in key_files:
        full_path = static_root / file_path
        static_files_status[file_path] = {
            'exists': full_path.exists(),
            'size': full_path.stat().st_size if full_path.exists() else 0,
            'path': str(full_path)
        }
    
    context = {
        'STATIC_URL': settings.STATIC_URL,
        'STATIC_ROOT': str(settings.STATIC_ROOT),
        'DEBUG': settings.DEBUG,
        'static_files_status': static_files_status,
        'request': request,
    }
    return render(request, 'core/test_static.html', context)

def test_404_error(request):
    """
    Test view to trigger a 404 error
    """
    from django.http import Http404
    raise Http404("This is a test 404 error")

def test_500_error(request):
    """
    Test view to trigger a 500 error
    """
    raise Exception("This is a test 500 error")

def test_403_error(request):
    """
    Test view to trigger a 403 error
    """
    from django.core.exceptions import PermissionDenied
    raise PermissionDenied("This is a test 403 error")

def test_400_error(request):
    """
    Test view to trigger a 400 error
    """
    from django.core.exceptions import BadRequest
    raise BadRequest("This is a test 400 error")