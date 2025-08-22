#!/usr/bin/env python3
"""
Demonstration script showing complete QR code workflow
"""

import os
import sys
import django
import json
import qrcode
from io import BytesIO
import base64

# Add the project directory to the Python path
sys.path.append('/c/Users/MOINAK/OneDrive/Desktop/TapNex/Tapnex/myproject')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from ticketing.models import Ticket

def demonstrate_qr_workflow():
    """Demonstrate the complete QR code generation and scanning workflow"""
    
    print("🎫 TapNex QR Code Workflow Demonstration")
    print("=" * 50)
    
    # Get a valid ticket for demonstration
    ticket = Ticket.objects.filter(status='VALID').first()
    if not ticket:
        # Create one from sold tickets
        ticket = Ticket.objects.filter(status='SOLD').first()
        if ticket:
            ticket.status = 'VALID'
            ticket.save()
            print(f"✅ Updated ticket {ticket.ticket_number} to VALID status")
        else:
            print("❌ No tickets available for demonstration")
            return
    
    print(f"\n📋 Ticket Information:")
    print(f"   Ticket Number: {ticket.ticket_number}")
    print(f"   Event: {ticket.event.title}")
    print(f"   Status: {ticket.status}")
    print(f"   Ticket Type: {ticket.ticket_type.type_name if ticket.ticket_type else 'General'}")
    
    # Generate QR code data (compact format)
    qr_data = {
        'tid': ticket.id,
        'tok': ticket.unique_secure_token
    }
    
    qr_json = json.dumps(qr_data)
    print(f"\n📱 QR Code Data (JSON):")
    print(f"   {qr_json}")
    
    # Legacy format support
    legacy_data = {
        'ticket_id': ticket.id,
        'unique_secure_token': ticket.unique_secure_token
    }
    
    legacy_json = json.dumps(legacy_data)
    print(f"\n📱 Legacy QR Code Data (Also Supported):")
    print(f"   {legacy_json}")
    
    # Generate actual QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_json)
    qr.make(fit=True)
    
    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR code image
    qr_filename = f"ticket_{ticket.ticket_number}_qr.png"
    img.save(qr_filename)
    print(f"\n🖼️  QR Code Image Generated: {qr_filename}")
    
    # Simulate API validation request
    print(f"\n🔍 Volunteer Scanner API Request Simulation:")
    print(f"   POST /api/validate-ticket/")
    print(f"   Content-Type: application/json")
    print(f"   Body: {qr_json}")
    
    # Show expected response for valid ticket
    expected_response = {
        "success": True,
        "message": "Ticket validated successfully",
        "ticket_number": ticket.ticket_number,
        "ticket_type_name": ticket.ticket_type.type_name if ticket.ticket_type else "General Admission",
        "entry_count": ticket.total_admission_count,
        "booking_quantity": ticket.booking_quantity,
        "event_name": ticket.event.title,
        "event_date": ticket.event.date.strftime('%B %d, %Y') if ticket.event else "Unknown Date"
    }
    
    print(f"\n✅ Expected API Response (First Scan):")
    print(json.dumps(expected_response, indent=2))
    
    # Show expected response for already used ticket
    already_used_response = {
        "success": False,
        "error_code": "ALREADY_USED",
        "message": "This ticket has already been used",
        "ticket_number": ticket.ticket_number,
        "ticket_type_name": ticket.ticket_type.type_name if ticket.ticket_type else "Unknown Type",
        "event_name": ticket.event.title if ticket.event else "Unknown Event",
        "used_at": "August 09, 2025 at 05:02 PM",
        "validated_by": "volunteer@example.com"
    }
    
    print(f"\n🚫 Expected API Response (Second Scan - Already Used):")
    print(json.dumps(already_used_response, indent=2))
    
    print(f"\n📱 Mobile Scanning Instructions:")
    print(f"   1. Login as volunteer at: http://127.0.0.1:8000/")
    print(f"   2. Go to Volunteer Dashboard")
    print(f"   3. Click 'Scan Tickets'")
    print(f"   4. Allow camera permissions")
    print(f"   5. Point camera at the generated QR code image")
    print(f"   6. Listen for success sound and see green confirmation")
    print(f"   7. Try scanning again to see 'Already Used' error")
    
    print(f"\n🔧 Manual Entry Testing:")
    print(f"   Ticket ID: {ticket.id}")
    print(f"   Security Token: {ticket.unique_secure_token}")
    print(f"   (Use these in manual entry form if QR code fails)")
    
    print(f"\n" + "=" * 50)
    print(f"🎉 QR Code workflow demonstration complete!")
    print(f"   QR code image saved as: {qr_filename}")
    print(f"   Ready for volunteer testing with mobile device")

if __name__ == "__main__":
    demonstrate_qr_workflow()
