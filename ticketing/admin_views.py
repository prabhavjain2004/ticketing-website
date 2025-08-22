from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.contrib import messages
from django.db import transaction
import csv
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Q, Count
from django.utils import timezone
from .models import Event, TicketType, Ticket, PromoCode, EventStaff, PromoCodeUsage, EventSponsor, EventCommission, Invoice, User
from .invoice_forms import EventCommissionForm
from .forms import (
    EventForm, AdminUserCreationForm, TicketForm, PromoCodeForm,
    EventStaffForm, TicketTypeForm, EventSponsorFormSet
)
from .utils import handle_event_csv_upload, generate_sample_csv

logger = logging.getLogger(__name__)

def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'

@login_required
@user_passes_test(is_admin)
def admin_delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    messages.success(request, 'Event deleted successfully!')
    return redirect('admin_event_list')
    
@login_required
@user_passes_test(is_admin)
def admin_event_commission(request, event_id):
    """Manage commission settings for an event"""
    event = get_object_or_404(Event, id=event_id)
    commission_settings, created = EventCommission.objects.get_or_create(
        event=event,
        defaults={
            'commission_type': 'percentage',
            'commission_value': 0,
            'created_by': request.user
        }
    )
    
    if request.method == 'POST':
        form = EventCommissionForm(request.POST, instance=commission_settings)
        if form.is_valid():
            commission = form.save(commit=False)
            commission.created_by = request.user
            commission.save()
            messages.success(request, f"Commission settings for {event.title} updated successfully.")
            return redirect('admin_event_detail', event_id=event_id)
    else:
        form = EventCommissionForm(instance=commission_settings)
    
    context = {
        'event': event,
        'form': form,
        'commission_settings': commission_settings,
    }
    
    return render(request, 'ticketing/admin/event_commission.html', context)

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Basic stats
    total_users = User.objects.count()
    total_events = Event.objects.count()
    total_tickets = Ticket.objects.count()
    active_users = User.objects.filter(is_active=True).count()

    # Recent events (last 5)
    events = Event.objects.order_by('-created_at')[:5]
    
    # Recent users (last 5)
    users = User.objects.order_by('-date_joined')[:5]

    context = {
        'total_users': total_users,
        'total_events': total_events,
        'total_tickets': total_tickets,
        'active_users': active_users,
        'events': events,
        'users': users,
        'user': request.user,
    }
    return render(request, 'core/admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_create_event(request):
    if request.method == 'POST':
        if 'csv_file' in request.FILES:
            csv_file = request.FILES['csv_file']
            # Accept any file as CSV (rely on content rather than extension)
            # This allows users to upload .txt files or other formats containing CSV data
            
            try:
                success, message, event_id = handle_event_csv_upload(csv_file, request.user)
                if success:
                    messages.success(request, message)
                    return redirect('admin_edit_event', event_id=event_id)
                else:
                    messages.error(request, message)
                    return redirect('admin_create_event')
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
                return redirect('admin_create_event')
        else:
            form = EventForm(request.POST, request.FILES)
            sponsor_formset = EventSponsorFormSet(request.POST, prefix='sponsors')
            
            if form.is_valid() and sponsor_formset.is_valid():
                event = form.save(commit=False)
                event.organizer = request.user
                event.save()
                
                # Save sponsors
                sponsor_formset.instance = event
                sponsor_formset.save()
                
                # Calculate total capacity from ticket quantities
                total_capacity = 0
                
                # Save ticket types
                for i in range(1, 5):  # Handle up to 4 ticket types
                    ticket_type = request.POST.get(f'ticket_type_{i}')
                    if ticket_type:  # If a ticket type name is provided
                        try:
                            price = request.POST.get(f'ticket_price_{i}', '0')
                            quantity = request.POST.get(f'ticket_quantity_{i}', '0')
                            
                            # Convert values with error handling
                            try:
                                price_value = float(price) if price else 0
                            except ValueError:
                                price_value = 0
                                
                            try:
                                quantity_value = int(quantity) if quantity else 0
                            except ValueError:
                                quantity_value = 0
                                
                            total_capacity += quantity_value
                            
                            TicketType.objects.create(
                                event=event,
                                type_name=ticket_type,
                                price=price_value,
                                quantity=quantity_value,
                                description=request.POST.get(f'ticket_description_{i}', '')
                            )
                        except Exception as e:
                            messages.warning(request, f"Issue with ticket type {i}: {str(e)}")
                
                # Ensure at least one ticket type exists
                if not event.ticket_types.exists():
                    TicketType.objects.create(
                        event=event,
                        type_name="General Admission",
                        price=0.00,
                        quantity=event.capacity or 100,
                        description="Default ticket type"
                    )
                    messages.info(request, "Created default ticket type for this event.")
                
                # Update event capacity if needed
                if total_capacity > 0:
                    event.capacity = total_capacity
                    event.save()
                    
                messages.success(request, 'Event created successfully!')
                return redirect('admin_event_list')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                
                if not sponsor_formset.is_valid():
                    messages.error(request, 'Please check the sponsor information.')
    else:
        form = EventForm()
        sponsor_formset = EventSponsorFormSet(prefix='sponsors')
    
    return render(request, 'core/admin/event_form.html', {
        'form': form,
        'sponsor_formset': sponsor_formset,
        'action': 'Create'
    })

@login_required
@user_passes_test(is_admin)
def admin_event_list(request):
    events = Event.objects.all().order_by('-created_at')
    return render(request, 'core/admin/event_list.html', {'events': events})

@login_required
@user_passes_test(is_admin)
def admin_edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        sponsor_formset = EventSponsorFormSet(request.POST, instance=event, prefix='sponsors')
        
        if form.is_valid() and sponsor_formset.is_valid():
            event = form.save()
            
            # Save sponsors
            sponsor_formset.save()
            
            messages.success(request, 'Event updated successfully!')
            return redirect('admin_event_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            
            if not sponsor_formset.is_valid():
                messages.error(request, 'Please check the sponsor information.')
    else:
        form = EventForm(instance=event)
        sponsor_formset = EventSponsorFormSet(instance=event, prefix='sponsors')
    
    return render(request, 'core/admin/event_form.html', {
        'form': form,
        'sponsor_formset': sponsor_formset,
        'action': 'Edit',
        'event': event
    })

# User Management Views
@login_required
@user_passes_test(is_admin)
def admin_user_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'core/admin/user_list.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def admin_create_user(request):
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            # Set role from form
            user.role = form.cleaned_data['role']
            user.save()
            messages.success(request, f'User created successfully with {user.get_role_display()} role!')
            return redirect('admin_user_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminUserCreationForm()
    return render(request, 'core/admin/user_form.html', {'form': form, 'action': 'Create'})

@login_required
@user_passes_test(is_admin)
def admin_edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        # Use custom form for handling password fields
        form = AdminUserCreationForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            updated_user = form.save(commit=False)
            # Set role from form
            updated_user.role = form.cleaned_data['role']
            
            # Check if password has been provided
            if form.cleaned_data.get('password1') and form.cleaned_data.get('password2'):
                # Password is being changed
                pass  # password will be set by form.save()
            else:
                # Keep existing password
                updated_user.password = user.password
                
            updated_user.save()
            messages.success(request, f'User updated successfully with {updated_user.get_role_display()} role!')
            return redirect('admin_user_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminUserCreationForm(instance=user)
    
    return render(request, 'core/admin/user_form.html', {'form': form, 'action': 'Edit'})

@login_required
@user_passes_test(is_admin)
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.id != request.user.id:
        user.delete()
        messages.success(request, 'User deleted successfully!')
    else:
        messages.error(request, 'You cannot delete your own account!')
    return redirect('admin_user_list')

# Ticket Management Views
@login_required
@user_passes_test(is_admin)
def admin_ticket_list(request):
    tickets = Ticket.objects.all().order_by('-purchase_date')
    return render(request, 'core/admin/ticket_list.html', {'tickets': tickets})

@login_required
@user_passes_test(is_admin)
def admin_create_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ticket created successfully!')
            return redirect('admin_ticket_list')
    else:
        form = TicketForm()
    return render(request, 'core/admin/ticket_form.html', {'form': form, 'action': 'Create'})

@login_required
@user_passes_test(is_admin)
def admin_edit_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ticket updated successfully!')
            return redirect('admin_ticket_list')
    else:
        form = TicketForm(instance=ticket)
    return render(request, 'core/admin/ticket_form.html', {'form': form, 'action': 'Edit'})

@login_required
@user_passes_test(is_admin)
def admin_delete_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    ticket.delete()
    messages.success(request, 'Ticket deleted successfully!')
    return redirect('admin_ticket_list')

@login_required
@user_passes_test(is_admin)
def admin_delete_all_tickets(request):
    """
    Delete all tickets in the system with proper confirmation
    """
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('admin_ticket_list')
    
    try:
        # Count tickets before deletion for reporting
        total_tickets = Ticket.objects.count()
        
        if total_tickets == 0:
            messages.warning(request, 'No tickets found to delete.')
            return redirect('admin_ticket_list')
        
        # Log the admin action for audit trail
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Admin {request.user.email} (ID: {request.user.id}) initiated deletion of ALL {total_tickets} tickets")
        
        # Delete all tickets
        with transaction.atomic():
            deleted_count, deleted_objects = Ticket.objects.all().delete()
            
        # Success message
        messages.success(
            request, 
            f'Successfully deleted {total_tickets} tickets. All ticket data has been permanently removed.'
        )
        
        # Log successful deletion
        logger.warning(f"Admin {request.user.email} successfully deleted {total_tickets} tickets")
        
    except Exception as e:
        # Log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error deleting all tickets by admin {request.user.email}: {str(e)}")
        
        messages.error(request, f'Error deleting tickets: {str(e)}')
    
    return redirect('admin_ticket_list')

# Promo Code Management Views
@login_required
@user_passes_test(is_admin)
def admin_promo_code_list(request):
    promo_codes = PromoCode.objects.all().order_by('-created_at')
    return render(request, 'core/admin/promo_code_list.html', {'promo_codes': promo_codes})

@login_required
@user_passes_test(is_admin)
def admin_create_promo_code(request):
    if request.method == 'POST':
        form = PromoCodeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Promo code created successfully!')
            return redirect('admin_promo_code_list')
    else:
        form = PromoCodeForm()
    return render(request, 'core/admin/promo_code_form.html', {'form': form, 'action': 'Create'})

@login_required
@user_passes_test(is_admin)
def admin_edit_promo_code(request, code_id):
    promo_code = get_object_or_404(PromoCode, id=code_id)
    if request.method == 'POST':
        form = PromoCodeForm(request.POST, instance=promo_code)
        if form.is_valid():
            form.save()
            messages.success(request, 'Promo code updated successfully!')
            return redirect('admin_promo_code_list')
    else:
        form = PromoCodeForm(instance=promo_code)
    return render(request, 'core/admin/promo_code_form.html', {'form': form, 'action': 'Edit'})

@login_required
@user_passes_test(is_admin)
def admin_delete_promo_code(request, code_id):
    promo_code = get_object_or_404(PromoCode, id=code_id)
    promo_code.delete()
    messages.success(request, 'Promo code deleted successfully!')
    return redirect('admin_promo_code_list')

# Staff Management Views
@login_required
@user_passes_test(is_admin)
def admin_staff_list(request):
    staff = EventStaff.objects.all().order_by('-assigned_at')
    return render(request, 'core/admin/staff_list.html', {'staff': staff})

@login_required
@user_passes_test(is_admin)
def admin_create_staff(request):
    # Check if event_id is provided in GET parameters
    event_id = request.GET.get('event_id')
    initial_data = {}
    
    # If event_id is provided, use it as initial value
    if event_id:
        try:
            event = Event.objects.get(id=event_id)
            initial_data['event'] = event.id
        except Event.DoesNotExist:
            pass
            
    if request.method == 'POST':
        form = EventStaffForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff member created successfully!')
            return redirect('admin_staff_list')
    else:
        form = EventStaffForm(initial=initial_data)
    
    return render(request, 'core/admin/staff_form.html', {'form': form, 'action': 'Create'})

@login_required
@user_passes_test(is_admin)
def admin_edit_staff(request, staff_id):
    staff = get_object_or_404(EventStaff, id=staff_id)
    if request.method == 'POST':
        form = EventStaffForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff member updated successfully!')
            return redirect('admin_staff_list')
    else:
        form = EventStaffForm(instance=staff)
    return render(request, 'core/admin/staff_form.html', {'form': form, 'action': 'Edit'})

@login_required
@user_passes_test(is_admin)
def admin_delete_staff(request, staff_id):
    staff = get_object_or_404(EventStaff, id=staff_id)
    staff.delete()
    messages.success(request, 'Staff member deleted successfully!')
    return redirect('admin_staff_list')

# Ticket Type Management Views
@login_required
@user_passes_test(is_admin)
def admin_ticket_type_list(request):
    ticket_types = TicketType.objects.all().order_by('event', 'type_name')
    events = Event.objects.all().order_by('title')
    return render(request, 'core/admin/ticket_type_list.html', {
        'ticket_types': ticket_types,
        'events': events
    })

@login_required
@user_passes_test(is_admin)
def admin_create_ticket_type(request):
    # Check if event_id is provided in GET parameters
    event_id = request.GET.get('event_id')
    event = None
    
    # If event_id is provided, get the event
    if event_id:
        event = get_object_or_404(Event, id=event_id)
        
    if request.method == 'POST':
        form = TicketTypeForm(request.POST, request.FILES)
        if form.is_valid():
            ticket_type = form.save(commit=False)
            
            # Template handling removed
            
            ticket_type.save()
            messages.success(request, 'Ticket type created successfully!')
            
            # If created from event form, redirect back to event edit
            if event_id:
                return redirect('admin_edit_event', event_id=event_id)
            else:
                return redirect('admin_ticket_type_list')
    else:
        # Pre-populate the event field if event_id is provided
        initial_data = {}
        if event:
            initial_data = {'event': event}
        
        form = TicketTypeForm(initial=initial_data)
    
    return render(request, 'core/admin/ticket_type_form.html', {
        'form': form, 
        'action': 'Create',
        'event': event
    })

@login_required
@user_passes_test(is_admin)
def admin_edit_ticket_type(request, type_id):
    ticket_type = get_object_or_404(TicketType, id=type_id)
    if request.method == 'POST':
        form = TicketTypeForm(request.POST, request.FILES, instance=ticket_type)
        if form.is_valid():
            updated_ticket_type = form.save(commit=False)
            
            # Template handling removed
            
            updated_ticket_type.save()
            messages.success(request, 'Ticket type updated successfully!')
            return redirect('admin_ticket_type_list')
    else:
        form = TicketTypeForm(instance=ticket_type)
    
    return render(request, 'core/admin/ticket_type_form.html', {
        'form': form, 
        'action': 'Edit',
        'ticket_type': ticket_type
    })

@login_required
@user_passes_test(is_admin)
def admin_delete_ticket_type(request, type_id):
    ticket_type = get_object_or_404(TicketType, id=type_id)
    ticket_type.delete()
    messages.success(request, 'Ticket type deleted successfully!')
    return redirect('admin_ticket_type_list')
    



# API Endpoints for Event and Ticket Type Management
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import os
from django.conf import settings
from django.core.files.storage import default_storage

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def api_create_event(request):
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        
        # Create new Event instance
        event = Event(
            title=data.get('title'),
            description=data.get('description'),
            short_description=data.get('short_description', ''),
            date=data.get('date'),
            end_date=data.get('end_date'),
            time=data.get('time'),
            end_time=data.get('end_time'),
            venue=data.get('venue'),
            venue_address=data.get('venue_address', ''),
            venue_map_link=data.get('venue_map_link', ''),
            capacity=data.get('capacity', 0),
            event_type=data.get('event_type', ''),
            registration_start_date=data.get('registration_start_date'),
            registration_deadline=data.get('registration_deadline'),
            organizer=request.user,
            status=data.get('status', 'DRAFT'),
            featured=data.get('featured', False),
            venue_terms=data.get('venue_terms', ''),
            event_terms=data.get('event_terms', ''),
            restrictions=data.get('restrictions', '')
        )
        
        # Handle banner image if included in multipart form data
        if 'banner_image' in request.FILES:
            banner_image = request.FILES['banner_image']
            filename = f"event_{data.get('title').replace(' ', '_')}{os.path.splitext(banner_image.name)[1]}"
            path = os.path.join('event_banners', filename)
            default_storage.save(path, banner_image)
            event.banner_image = path
        
        event.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Event created successfully',
            'event_id': event.id
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating event: {str(e)}'
        }, status=400)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["PUT", "PATCH"])
def api_update_event(request, event_id):
    try:
        event = get_object_or_404(Event, id=event_id)
        data = json.loads(request.body)
        
        # Update event fields if provided
        if 'title' in data:
            event.title = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'short_description' in data:
            event.short_description = data['short_description']
        if 'date' in data:
            event.date = data['date']
        if 'end_date' in data:
            event.end_date = data['end_date']
        if 'time' in data:
            event.time = data['time']
        if 'end_time' in data:
            event.end_time = data['end_time']
        if 'venue' in data:
            event.venue = data['venue']
        if 'venue_address' in data:
            event.venue_address = data['venue_address']
        if 'venue_map_link' in data:
            event.venue_map_link = data['venue_map_link']
        if 'capacity' in data:
            event.capacity = data['capacity']
        if 'event_type' in data:
            event.event_type = data['event_type']
        if 'registration_start_date' in data:
            event.registration_start_date = data['registration_start_date']
        if 'registration_deadline' in data:
            event.registration_deadline = data['registration_deadline']
        if 'status' in data:
            event.status = data['status']
        if 'featured' in data:
            event.featured = data['featured']
        if 'venue_terms' in data:
            event.venue_terms = data['venue_terms']
        if 'event_terms' in data:
            event.event_terms = data['event_terms']
        if 'restrictions' in data:
            event.restrictions = data['restrictions']
        
        # Handle banner image if included in multipart form data
        if 'banner_image' in request.FILES:
            # Delete old banner if exists
            if event.banner_image:
                old_path = event.banner_image.path
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            banner_image = request.FILES['banner_image']
            filename = f"event_{event.id}_{event.title.replace(' ', '_')}{os.path.splitext(banner_image.name)[1]}"
            path = os.path.join('event_banners', filename)
            default_storage.save(path, banner_image)
            event.banner_image = path
        
        event.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Event updated successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating event: {str(e)}'
        }, status=400)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def api_create_ticket_type(request, event_id):
    try:
        event = get_object_or_404(Event, id=event_id)
        
        # Check if request is multipart form data or JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Create a form instance with POST data and FILES
            form_data = request.POST.copy()
            form_data['event'] = event.id  # Ensure the event is set
            
            form = TicketTypeForm(form_data, request.FILES)
            
            if form.is_valid():
                ticket_type = form.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Ticket type created successfully',
                    'ticket_type_id': ticket_type.id,
                    'ticket_type': {
                        'id': ticket_type.id,
                        'type_name': ticket_type.type_name,
                        'price': float(ticket_type.price),
                        'quantity': ticket_type.quantity,
                        'attendees_per_ticket': ticket_type.attendees_per_ticket,

                    }
                })
            else:
                # Return form validation errors
                errors = dict([(key, [str(error) for error in errors_list]) 
                          for key, errors_list in form.errors.items()])
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid form data',
                    'errors': errors
                }, status=400)
        else:
            # Handle JSON data
            data = json.loads(request.body)
            data['event'] = event.id  # Ensure the event is set
            
            form = TicketTypeForm(data)
            if form.is_valid():
                ticket_type = form.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Ticket type created successfully',
                    'ticket_type_id': ticket_type.id
                })
            else:
                # Return form validation errors
                errors = dict([(key, [str(error) for error in errors_list]) 
                          for key, errors_list in form.errors.items()])
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid form data',
                    'errors': errors
                }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating ticket type: {str(e)}'
        }, status=400)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["PUT", "PATCH", "POST"])  # Allow POST for form submissions
def api_update_ticket_type(request, type_id):
    try:
        ticket_type = get_object_or_404(TicketType, id=type_id)
        
        # Check if request is multipart form data or JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            # For PATCH/PUT with form-data, we need to handle it specially
            if request.method in ['PATCH', 'PUT']:
                data = request.POST.copy()
                # Only update the fields that are provided
                instance_data = {
                    'event': ticket_type.event.id,
                    'type_name': ticket_type.type_name,
                    'price': ticket_type.price,
                    'quantity': ticket_type.quantity,
                    'description': ticket_type.description,
                    'attendees_per_ticket': ticket_type.attendees_per_ticket,
                    'image_template_url': ticket_type.image_template_url
                }
                
                # Update with provided data
                for key in data:
                    if key in instance_data and key != 'event':  # Don't allow changing event
                        instance_data[key] = data[key]
                
                form = TicketTypeForm(instance_data, request.FILES, instance=ticket_type)
            else:  # POST
                form = TicketTypeForm(request.POST, request.FILES, instance=ticket_type)
            
            if form.is_valid():
                updated_ticket_type = form.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Ticket type updated successfully',
                    'ticket_type': {
                        'id': updated_ticket_type.id,
                        'type_name': updated_ticket_type.type_name,
                        'price': float(updated_ticket_type.price),
                        'quantity': updated_ticket_type.quantity,
                        'attendees_per_ticket': updated_ticket_type.attendees_per_ticket,

                    }
                })
            else:
                # Return form validation errors
                errors = dict([(key, [str(error) for error in errors_list]) 
                          for key, errors_list in form.errors.items()])
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid form data',
                    'errors': errors
                }, status=400)
        else:
            # Handle JSON data
            data = json.loads(request.body)
            instance_data = {
                'event': ticket_type.event.id
            }
            
            # Only update fields that are provided in the request
            if 'type_name' in data:
                instance_data['type_name'] = data['type_name']
            if 'price' in data:
                instance_data['price'] = data['price']
            if 'quantity' in data:
                instance_data['quantity'] = data['quantity']
            if 'description' in data:
                instance_data['description'] = data['description']
            if 'attendees_per_ticket' in data:
                instance_data['attendees_per_ticket'] = data['attendees_per_ticket']
            
            form = TicketTypeForm(instance_data, instance=ticket_type)
            
            if form.is_valid():
                updated_ticket_type = form.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Ticket type updated successfully'
                })
            else:
                # Return form validation errors
                errors = dict([(key, [str(error) for error in errors_list]) 
                          for key, errors_list in form.errors.items()])
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid form data',
                    'errors': errors
                }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating ticket type: {str(e)}'
        }, status=400)

@login_required
@user_passes_test(is_admin)
def download_sample_csv(request):
    """Download instructions for CSV event creation as a text file."""
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="csv_instructions.txt"'
    response['Cache-Control'] = 'no-cache'
    
    # Read the instructions from the markdown file
    import os
    from django.conf import settings
    
    instructions_path = os.path.join(settings.BASE_DIR, 'ticketing/static/core/docs/csv_upload_guide.md')
    detailed_instructions_path = os.path.join(settings.BASE_DIR, 'ticketing/static/core/docs/csv_instructions.md')
    
    try:
        with open(detailed_instructions_path, 'r', encoding='utf-8') as file:
            instructions = file.read()
    except FileNotFoundError:
        try:
            with open(instructions_path, 'r', encoding='utf-8') as file:
                instructions = file.read()
        except FileNotFoundError:
            instructions = "# CSV Upload Instructions\n\nPlease refer to the documentation for detailed instructions on how to format your CSV file."
    
    # Add a sample CSV content at the end of the instructions
    instructions += "\n\n## Sample CSV Content\n\n```csv\n"
    csv_content = generate_sample_csv()
    instructions += csv_content + "\n```"
    
    response.write(instructions)
    return response

# Promo Code Analytics Views
@login_required
@user_passes_test(is_admin)
def admin_promo_code_analytics(request):
    """Admin dashboard for promo code analytics"""
    promo_codes = PromoCode.objects.all().order_by('-created_at')
    
    # Enhance promo codes with analytics data (now filtering for successful, non-sandbox transactions)
    for promo_code in promo_codes:
        # Only count successful, non-sandbox transactions
        successful_usages = promo_code.promo_code_usages.filter(
            ticket__purchase_transaction__status='SUCCESS'
        ).exclude(
            ticket__purchase_transaction__payment_gateway='SANDBOX'
        )
        
        promo_code.usage_count = successful_usages.count()
        promo_code.tickets_booked = promo_code.total_tickets_booked()
        promo_code.amount_saved = promo_code.total_amount_saved()
        promo_code.revenue_generated = promo_code.total_revenue_generated()
        promo_code.average_order_value = promo_code.average_order_value()
        promo_code.redemption_rate = promo_code.redemption_rate()
    
    return render(request, 'core/admin/promo_code_analytics.html', {
        'promo_codes': promo_codes
    })

@login_required
def organizer_promo_code_analytics(request):
    """Organizer dashboard for promo code analytics for their events"""
    # Get events where this user is an organizer (either directly or through EventStaff model)
    organizer_events = list(Event.objects.filter(organizer=request.user))
    staff_events = list(Event.objects.filter(staff__user=request.user, staff__role='ORGANIZER'))
    
    # Combine both event lists (removing duplicates)
    all_events = list(set(organizer_events + staff_events))
    
    # Get all promo codes for these events
    promo_codes = PromoCode.objects.filter(event__in=all_events).order_by('-created_at')
    
    # Initialize aggregate totals
    total_active_promos = 0
    total_saved = 0
    total_revenue = 0
    total_redemptions = 0
    total_max_uses = 0
    
    # Enhance promo codes with analytics data and calculate aggregate totals
    for promo_code in promo_codes:
        # Only count successful, non-sandbox transactions
        successful_usages = promo_code.promo_code_usages.filter(
            ticket__purchase_transaction__status='SUCCESS'
        ).exclude(
            ticket__purchase_transaction__payment_gateway='SANDBOX'
        )
        
        promo_code.usage_count = successful_usages.count()
        promo_code.tickets_booked = promo_code.total_tickets_booked()
        promo_code.amount_saved = promo_code.total_amount_saved()
        promo_code.revenue_generated = promo_code.total_revenue_generated()
        promo_code.average_order_value = promo_code.average_order_value()
        promo_code.redemption_rate = promo_code.redemption_rate()
        
        # Add to aggregate totals
        if promo_code.is_active and promo_code.is_valid:
            total_active_promos += 1
            
        total_saved += float(promo_code.amount_saved)
        total_revenue += float(promo_code.revenue_generated)
        total_redemptions += promo_code.usage_count
        
        if promo_code.max_uses > 0:
            total_max_uses += promo_code.max_uses
    
    # Calculate average redemption rate
    if total_max_uses > 0:
        avg_redemption_rate = (total_redemptions / total_max_uses) * 100
    else:
        avg_redemption_rate = 0
    
    return render(request, 'core/organizer_promo_code_analytics.html', {
        'promo_codes': promo_codes,
        'total_active_promos': total_active_promos,
        'total_saved': total_saved,
        'total_revenue': total_revenue,
        'avg_redemption_rate': avg_redemption_rate,
        'all_events': all_events,
    })
    
@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def api_get_event_ticket_types(request, event_id):
    """API endpoint to get all ticket types for an event"""
    try:
        event = get_object_or_404(Event, id=event_id)
        ticket_types = event.ticket_types.all()
        
        result = []
        for ticket_type in ticket_types:
            result.append({
                'id': ticket_type.id,
                'type_name': ticket_type.type_name,
                'price': float(ticket_type.price),
                'quantity': ticket_type.quantity,
                'description': ticket_type.description,
                'attendees_per_ticket': ticket_type.attendees_per_ticket,
                'image_template_url': ticket_type.image_template_url or ''
            })
            
        return JsonResponse({
            'success': True,
            'ticket_types': result
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error fetching ticket types: {str(e)}'
        }, status=400)

import csv
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.http import HttpResponse, JsonResponse


@login_required
@user_passes_test(is_admin)
def invoice_dashboard(request):
    """
    Admin dashboard for invoice management
    """
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    event_id = request.GET.get('event')
    search_query = request.GET.get('search')
    
    # Base queryset
    invoices = Invoice.objects.select_related(
        'event', 'user', 'ticket', 'ticket_type', 'transaction'
    ).order_by('-created_at')
    
    # Apply filters
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            invoices = invoices.filter(created_at__date__gte=start_date)
        except ValueError:
            messages.error(request, "Invalid start date format")
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            invoices = invoices.filter(created_at__date__lte=end_date)
        except ValueError:
            messages.error(request, "Invalid end date format")
    
    if event_id:
        invoices = invoices.filter(event_id=event_id)
    
    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query) |
            Q(ticket__ticket_number__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(event__title__icontains=search_query) |
            Q(transaction__transaction_id__icontains=search_query)
        )
    
    # Calculate revenue summary
    total_revenue = invoices.aggregate(
        total_commission=Sum('commission')
    )['total_commission'] or Decimal('0.00')
    
    total_invoices = invoices.count()
    total_amount = invoices.aggregate(
        total_amount=Sum('total_price')
    )['total_amount'] or Decimal('0.00')
    
    # Get events for filter dropdown
    events = Event.objects.filter(invoices__isnull=False).distinct().order_by('title')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(invoices, 25)  # Show 25 invoices per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_revenue': total_revenue,
        'total_invoices': total_invoices,
        'total_amount': total_amount,
        'events': events,
        'filters': {
            'start_date': start_date,
            'end_date': end_date,
            'event_id': event_id,
            'search_query': search_query,
        }
    }
    
    return render(request, 'ticketing/admin/invoice_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def invoice_detail(request, invoice_id):
    """
    Detailed view of a specific invoice
    """
    try:
        invoice = Invoice.objects.select_related(
            'event', 'user', 'ticket', 'ticket_type', 'transaction'
        ).get(id=invoice_id)
    except Invoice.DoesNotExist:
        messages.error(request, "Invoice not found")
        return redirect('invoice_dashboard')
    
    context = {
        'invoice': invoice,
    }
    
    return render(request, 'ticketing/admin/invoice_detail.html', context)

@login_required
@user_passes_test(is_admin)
def export_invoices_csv(request):
    """
    Export invoices to CSV format
    """
    # Get filter parameters (same as dashboard)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    event_id = request.GET.get('event')
    search_query = request.GET.get('search')
    
    # Base queryset
    invoices = Invoice.objects.select_related(
        'event', 'user', 'ticket', 'ticket_type', 'transaction'
    ).order_by('-created_at')
    
    # Apply filters
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            invoices = invoices.filter(created_at__date__gte=start_date)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            invoices = invoices.filter(created_at__date__lte=end_date)
        except ValueError:
            pass
    
    if event_id:
        invoices = invoices.filter(event_id=event_id)
    
    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query) |
            Q(ticket__ticket_number__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(event__title__icontains=search_query) |
            Q(transaction__transaction_id__icontains=search_query)
        )
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="invoices_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Invoice Number',
        'Event Name',
        'Ticket ID',
        'Customer Email',
        'Ticket Type',
        'Base Price (₹)',
        'TapNex Service Fee (₹)',
        'Total Paid (₹)',
        'Purchase Date & Time',
        'Transaction ID',
        'Order ID',
    ])
    
    # Write data
    for invoice in invoices:
        writer.writerow([
            invoice.invoice_number,
            invoice.event.title,
            invoice.ticket.ticket_number,
            invoice.user.email,
            invoice.ticket_type.type_name,
            invoice.base_price,
            invoice.commission,
            invoice.total_price,
            invoice.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            invoice.transaction.transaction_id or 'N/A',
            invoice.transaction.order_id,
        ])
    
    return response

@login_required
@user_passes_test(is_admin)
def invoice_analytics(request):
    """
    Analytics view for invoice data
    """
    # Date range for analytics (last 30 days by default)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Get date range from request
    if request.GET.get('start_date'):
        try:
            start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if request.GET.get('end_date'):
        try:
            end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Get invoices in date range
    invoices = Invoice.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).select_related('event')
    
    # Calculate analytics
    total_revenue = invoices.aggregate(
        total_commission=Sum('commission')
    )['total_commission'] or Decimal('0.00')
    
    total_invoices = invoices.count()
    total_amount = invoices.aggregate(
        total_amount=Sum('total_price')
    )['total_amount'] or Decimal('0.00')
    
    # Revenue by event
    revenue_by_event = invoices.values('event__title').annotate(
        total_commission=Sum('commission'),
        total_amount=Sum('total_price'),
        invoice_count=Count('id')
    ).order_by('-total_commission')
    
    # Daily revenue for chart
    daily_revenue = invoices.extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        daily_commission=Sum('commission'),
        daily_amount=Sum('total_price')
    ).order_by('day')
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        'total_invoices': total_invoices,
        'total_amount': total_amount,
        'revenue_by_event': revenue_by_event,
        'daily_revenue': list(daily_revenue),
    }
    
    return render(request, 'ticketing/admin/invoice_analytics.html', context)

@login_required
@user_passes_test(is_admin)
def event_commission_management(request):
    """
    Manage commission settings for events
    """
    from .models import EventCommission
    
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        commission_type = request.POST.get('commission_type')
        commission_value = request.POST.get('commission_value')
        
        try:
            event = Event.objects.get(id=event_id)
            commission_value = Decimal(commission_value)
            
            if commission_value < 0:
                messages.error(request, "Commission value cannot be negative")
                return redirect('event_commission_management')
            
            # Update or create commission settings
            commission_settings, created = EventCommission.objects.update_or_create(
                event=event,
                defaults={
                    'commission_type': commission_type,
                    'commission_value': commission_value,
                    'created_by': request.user,
                }
            )
            
            action = "created" if created else "updated"
            messages.success(request, f"Commission settings {action} for {event.title}")
            
        except (Event.DoesNotExist, ValueError) as e:
            messages.error(request, f"Error: {str(e)}")
    
    # Get all events with their commission settings
    events = Event.objects.prefetch_related('commission_settings').order_by('title')
    
    context = {
        'events': events,
    }
    
    return render(request, 'ticketing/admin/event_commission.html', context)

@login_required
@user_passes_test(is_admin)
def admin_volunteer_statistics(request):
    """Admin view for volunteer ticket scanning statistics"""
    from django.db.models import Count, Q
    from datetime import date, timedelta
    
    # Get filter parameters
    date_filter = request.GET.get('date_filter', 'today')
    event_id = request.GET.get('event_id')
    volunteer_id = request.GET.get('volunteer_id')
    
    # Base queryset for volunteers
    volunteers = User.objects.filter(role='VOLUNTEER').select_related()
    
    # Date filtering
    today = date.today()
    if date_filter == 'today':
        start_date = today
        end_date = today
    elif date_filter == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
    elif date_filter == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    elif date_filter == 'month':
        start_date = today - timedelta(days=30)
        end_date = today
    else:  # all time
        start_date = None
        end_date = None
    
    # Build ticket queryset with filters
    ticket_filters = Q(validated_by__role='VOLUNTEER')
    
    if start_date and end_date:
        ticket_filters &= Q(used_at__date__range=[start_date, end_date])
    
    if event_id:
        ticket_filters &= Q(event_id=event_id)
    
    if volunteer_id:
        ticket_filters &= Q(validated_by_id=volunteer_id)
    
    # Get all tickets validated by volunteers with the filters
    validated_tickets = Ticket.objects.filter(ticket_filters).select_related(
        'validated_by', 'event', 'ticket_type'
    ).order_by('-used_at')
    
    # Calculate statistics for each volunteer
    volunteer_stats = []
    for volunteer in volunteers:
        volunteer_tickets = validated_tickets.filter(validated_by=volunteer)
        
        # Calculate basic stats
        total_scanned = volunteer_tickets.count()
        valid_entries = volunteer_tickets.filter(status='USED').count()
        
        # Calculate total attendees (considering tickets with multiple attendees)
        total_attendees = sum(
            ticket.total_admission_count or 1 
            for ticket in volunteer_tickets
        )
        
        # Get recent scans (last 10)
        recent_scans = volunteer_tickets[:10]
        
        # Get event breakdown
        event_breakdown = {}
        for ticket in volunteer_tickets:
            event_name = ticket.event.title if ticket.event else 'Unknown Event'
            if event_name not in event_breakdown:
                event_breakdown[event_name] = {
                    'count': 0,
                    'attendees': 0
                }
            event_breakdown[event_name]['count'] += 1
            event_breakdown[event_name]['attendees'] += ticket.total_admission_count or 1
        
        # Convert to list for easier JSON serialization
        event_breakdown_list = [
            {'event_name': k, 'count': v['count'], 'attendees': v['attendees']} 
            for k, v in event_breakdown.items()
        ]
        
        # Only include volunteers who have scanned tickets (if filtering)
        if volunteer_id and str(volunteer.id) != volunteer_id:
            continue
            
        if total_scanned > 0 or not any([date_filter != 'all', event_id, volunteer_id]):
            volunteer_stats.append({
                'volunteer': volunteer,
                'total_scanned': total_scanned,
                'valid_entries': valid_entries,
                'total_attendees': total_attendees,
                'recent_scans': recent_scans,
                'event_breakdown': event_breakdown,
                'event_breakdown_list': event_breakdown_list,
                'last_scan': volunteer_tickets.first().used_at if volunteer_tickets.exists() else None
            })
    
    # Sort by total scanned (most active first)
    volunteer_stats.sort(key=lambda x: x['total_scanned'], reverse=True)
    
    # Get events for filter dropdown
    events = Event.objects.all().order_by('title')
    
    # Get volunteers for filter dropdown  
    active_volunteers = User.objects.filter(
        role='VOLUNTEER',
        validated_tickets__isnull=False
    ).distinct().order_by('first_name', 'last_name', 'email')
    
    # Calculate summary statistics
    total_scanned_all = validated_tickets.count()
    total_attendees_all = sum(
        ticket.total_admission_count or 1 
        for ticket in validated_tickets
    )
    active_volunteers_count = len([v for v in volunteer_stats if v['total_scanned'] > 0])
    
    context = {
        'volunteer_stats': volunteer_stats,
        'events': events,
        'active_volunteers': active_volunteers,
        'filters': {
            'date_filter': date_filter,
            'event_id': int(event_id) if event_id else None,
            'volunteer_id': int(volunteer_id) if volunteer_id else None,
        },
        'summary': {
            'total_scanned': total_scanned_all,
            'total_attendees': total_attendees_all,
            'active_volunteers': active_volunteers_count,
            'total_volunteers': volunteers.count(),
        },
        'date_range_text': _get_date_range_text(date_filter, start_date, end_date),
    }
    
    return render(request, 'core/admin/volunteer_statistics.html', context)

def _get_date_range_text(date_filter, start_date, end_date):
    """Helper function to get human-readable date range text"""
    if date_filter == 'today':
        return 'Today'
    elif date_filter == 'yesterday':
        return 'Yesterday'
    elif date_filter == 'week':
        return 'Last 7 days'
    elif date_filter == 'month':
        return 'Last 30 days'
    else:
        return 'All time'
