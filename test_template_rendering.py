#!/usr/bin/env python3
"""
Test the actual HTML output of our event banner template tag
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from django.template import Template, Context
from ticketing.models import Event

def test_template_rendering():
    """Test the actual template rendering"""
    print("🎭 Testing Template Rendering")
    print("=" * 40)
    
    # Get the event
    event = Event.objects.first()
    if not event:
        print("❌ No events found")
        return
    
    print(f"📅 Event: {event.title}")
    print(f"🔗 Banner URL: {event.banner_image_url[:80]}...")
    
    # Test the template tag directly
    template_content = """
    {% load ticketing_extras %}
    {% google_drive_image event.banner_image_url event.title "w-full h-96 object-cover" %}
    """
    
    template = Template(template_content)
    context = Context({'event': event})
    rendered = template.render(context)
    
    print("\n🏷️  Rendered HTML:")
    print(rendered.strip())
    
    # Test the event detail template structure
    event_detail_template = """
    {% load ticketing_extras %}
    <div class="event-banner">
        {% if event.banner_image_url %}
            <div class="relative h-96">
                {% google_drive_image event.banner_image_url event.title "w-full h-full object-cover" %}
                <div class="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
            </div>
        {% else %}
            <div class="h-96 bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
                <p class="text-white text-xl">No Banner Image</p>
            </div>
        {% endif %}
    </div>
    """
    
    template2 = Template(event_detail_template)
    rendered2 = template2.render(context)
    
    print("\n🎨 Event Detail Template Output:")
    print(rendered2.strip())

if __name__ == "__main__":
    test_template_rendering()
