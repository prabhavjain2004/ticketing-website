#!/usr/bin/env python3
"""
Test script to verify event banner images are working correctly
"""
import os
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from ticketing.models import Event
from ticketing.google_drive_utils import extract_google_drive_id, get_google_drive_lh3_url
from ticketing.templatetags.ticketing_extras import google_drive_image

def test_event_banner_images():
    """Test all event banner images"""
    print("🔍 Testing Event Banner Images")
    print("=" * 50)
    
    events = Event.objects.all()
    
    if not events:
        print("❌ No events found in database")
        return
    
    for event in events:
        print(f"\n📅 Event: {event.title}")
        print(f"📋 Status: {event.status}")
        
        if not event.banner_image_url:
            print("❌ No banner image URL configured")
            continue
            
        print(f"📄 Banner URL/Iframe: {event.banner_image_url[:100]}...")
        
        # Test file ID extraction
        file_id = extract_google_drive_id(event.banner_image_url)
        if file_id:
            print(f"🆔 Extracted File ID: {file_id}")
            
            # Test different URL formats
            lh3_url = get_google_drive_lh3_url(file_id, 1200)
            print(f"🔗 LH3 URL: {lh3_url}")
            
            # Test URL accessibility
            try:
                response = requests.head(lh3_url, timeout=10)
                if response.status_code == 200:
                    print(f"✅ Image accessible (Status: {response.status_code})")
                    print(f"📏 Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
                    print(f"📦 Content-Length: {response.headers.get('Content-Length', 'Unknown')} bytes")
                else:
                    print(f"⚠️  Image response (Status: {response.status_code})")
            except requests.RequestException as e:
                print(f"❌ Failed to access image: {e}")
            
            # Test template tag
            html_result = google_drive_image(event.banner_image_url, event.title, "test-class", size=1200)
            print(f"🏷️  Template tag result: {html_result[:100]}...")
            
        else:
            print("❌ Could not extract file ID from URL")
        
        print("-" * 30)

if __name__ == "__main__":
    test_event_banner_images()
