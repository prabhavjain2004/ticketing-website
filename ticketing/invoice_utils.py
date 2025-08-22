import io
import logging
import os
from decimal import Decimal
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from .models import Invoice, EventCommission

logger = logging.getLogger(__name__)

def calculate_commission(event, total_price, attendee_count=1):
    """
    Calculate commission based on event commission settings.
    For fixed commission, it's calculated per attendee.
    For percentage commission, it's calculated on total price.
    """
    try:
        commission_settings = event.commission_settings
        commission = commission_settings.calculate_commission(total_price, attendee_count)
        return Decimal(str(commission))
    except EventCommission.DoesNotExist:
        # No commission settings found, return 0
        return Decimal('0.00')

def generate_invoice_pdf(invoice):
    """
    Generate PDF invoice for the given invoice object
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    
    # Add NexGen FC Logo from Google Drive
    try:
        import requests
        from io import BytesIO
        
        # Google Drive direct download URL for the logo
        # Replace this with your actual Google Drive file ID
        logo_drive_id = "1giAtj3jwPxY7z-MI9vpc1Ep7RsJaLeeb"  # Update this with actual file ID
        logo_url = f"https://drive.google.com/uc?export=download&id={logo_drive_id}"
        
        # Download logo from Google Drive
        response = requests.get(logo_url, timeout=10)
        if response.status_code == 200:
            logo_data = BytesIO(response.content)
            logo = Image(logo_data, width=1*inch, height=1*inch)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 10))
            logger.info("Successfully loaded NexGen FC logo from Google Drive")
        else:
            logger.warning(f"Failed to download logo from Google Drive: HTTP {response.status_code}")
    except Exception as e:
        logger.warning(f"Could not load NexGen FC logo from Google Drive: {e}")
        # Fallback to local file if Google Drive fails
        try:
            logo_path = os.path.join(settings.STATIC_ROOT, 'core', 'images', 'LOGO_NEXGEN_FC.png')
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=1*inch, height=1*inch)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 10))
                logger.info("Fallback: Loaded logo from local static files")
        except Exception as fallback_e:
            logger.warning(f"Fallback logo loading also failed: {fallback_e}")
    
    # Title
    story.append(Paragraph("TICKET INVOICE", title_style))
    story.append(Spacer(1, 20))
    
    # Event and Ticket Information
    story.append(Paragraph("Event Details", heading_style))
    
    event_data = [
        ['Event Name:', invoice.event.title],
        ['Ticket ID:', invoice.ticket.ticket_number],
        ['Ticket Type:', invoice.ticket_type.type_name],
        ['Customer:', invoice.user.email],
    ]
    
    event_table = Table(event_data, colWidths=[2*inch, 4*inch])
    event_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(event_table)
    story.append(Spacer(1, 20))
    
    # Pricing Breakdown
    story.append(Paragraph("Pricing Breakdown", heading_style))
    
    pricing_data = [
        ['Description', 'Amount (Rs.)'],
        ['Base Ticket Price', f"Rs. {invoice.base_price}"],
        ['TapNex Service Fee', f"Rs. {invoice.commission}"],
        ['', ''],
        ['Total Paid', f"Rs. {invoice.total_price}"],
    ]
    
    pricing_table = Table(pricing_data, colWidths=[4*inch, 2*inch])
    pricing_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -2), 'Helvetica'),
        ('FONTNAME', (1, 1), (1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
    ]))
    story.append(pricing_table)
    story.append(Spacer(1, 20))
    
    # Transaction Details
    story.append(Paragraph("Transaction Details", heading_style))
    
    transaction_data = [
        ['Invoice Number:', invoice.invoice_number],
        ['Transaction ID:', invoice.transaction.transaction_id or 'N/A'],
        ['Order ID:', invoice.transaction.order_id],
        ['Date of Purchase:', invoice.created_at.strftime('%Y-%m-%d %H:%M:%S')],
    ]
    
    transaction_table = Table(transaction_data, colWidths=[2*inch, 4*inch])
    transaction_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(transaction_table)
    story.append(Spacer(1, 30))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.darkblue,
        spaceBefore=20
    )
    story.append(Paragraph("Paid To: NexGen FC", footer_style))
    story.append(Spacer(1, 5))
    story.append(Paragraph("A premium brand by NexGen FC", footer_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Thank you for using TapNex!", footer_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def send_invoice_email(invoice, force_send=False):
    """
    Send invoice PDF via email to the customer
    Prevents duplicate emails unless force_send is True
    """
    try:
        # Check if this is an existing invoice that may have already been emailed
        if not force_send and invoice.pk:
            # Check when the invoice was created - if it's not recent, it was likely already emailed
            from django.utils import timezone
            from datetime import timedelta
            
            if invoice.created_at < timezone.now() - timedelta(minutes=5):
                logger.info(f"Skipping email for existing invoice {invoice.invoice_number} - likely already sent")
                return True
        
        # Generate PDF
        pdf_buffer = generate_invoice_pdf(invoice)
        
        # Email subject and content
        subject = f"Invoice for {invoice.event.title} - {invoice.invoice_number}"
        
        # Get logo for email
        from .utils import get_logo_base64
        logo_base64 = get_logo_base64()
        
        # HTML email content
        html_content = render_to_string('ticketing/emails/invoice_email.html', {
            'invoice': invoice,
            'event': invoice.event,
            'user': invoice.user,
            'logo_base64': logo_base64,
        })
        
        # Plain text content
        text_content = f"""
        Invoice for {invoice.event.title}
        
        Invoice Number: {invoice.invoice_number}
        Ticket ID: {invoice.ticket.ticket_number}
        Total Amount: ₹{invoice.total_price}
        
        Please find the attached invoice for your ticket purchase.
        
        Thank you for using TapNex!
        """
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[invoice.user.email]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Attach PDF
        email.attach(
            f"invoice_{invoice.invoice_number}.pdf",
            pdf_buffer.getvalue(),
            'application/pdf'
        )
        
        # Send email
        email.send()
        
        logger.info(f"Invoice email sent successfully for invoice {invoice.invoice_number}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending invoice email for invoice {invoice.invoice_number}: {str(e)}")
        return False

def create_invoice_for_ticket(ticket, payment_transaction):
    """
    Create invoice record for a ticket purchase
    Prevents duplicate invoices by checking if one already exists
    """
    try:
        # Check if invoice already exists for this ticket
        existing_invoice = Invoice.objects.filter(
            ticket=ticket,
            transaction=payment_transaction
        ).first()
        
        if existing_invoice:
            logger.info(f"Invoice already exists for ticket {ticket.ticket_number}: {existing_invoice.invoice_number}")
            return existing_invoice
        
        # Get attendee count from ticket type (default to 1 if not set)
        attendee_count = getattr(ticket.ticket_type, 'attendees_per_ticket', 1)
        
        # Calculate commission based on total price and attendee count
        commission = calculate_commission(ticket.event, payment_transaction.amount, attendee_count)
        base_price = payment_transaction.amount - commission
        
        # Create invoice
        invoice = Invoice.objects.create(
            ticket=ticket,
            user=ticket.customer,
            event=ticket.event,
            ticket_type=ticket.ticket_type,
            transaction=payment_transaction,
            base_price=base_price,
            commission=commission,
            total_price=payment_transaction.amount,
        )
        
        logger.info(f"Invoice created successfully: {invoice.invoice_number} with {attendee_count} attendees (base: {base_price}, commission: {commission}, total: {payment_transaction.amount})")
        return invoice
        
    except Exception as e:
        logger.error(f"Error creating invoice for ticket {ticket.ticket_number}: {str(e)}", exc_info=True)
        return None
