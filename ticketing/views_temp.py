@login_required
@user_passes_test(lambda u: u.role == 'ORGANIZER')
def download_organizer_report(request):
    """Download a comprehensive CSV report of all events and ticket sales for an organizer"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="organizer_report_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Event Title', 'Event Date', 'Ticket Type', 'Ticket Number', 
        'Customer Email', 'Customer Name', 'Purchase Date', 'Price', 
        'Status', 'Check-in Time', 'Attendees'
    ])
    
    # Get all events for this organizer
    events = Event.objects.filter(organizer=request.user)
    
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
