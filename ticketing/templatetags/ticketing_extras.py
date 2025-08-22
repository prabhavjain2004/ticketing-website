from django import template
from django.utils.safestring import mark_safe
from ..google_drive_utils import get_drive_image_url, extract_google_drive_id, get_google_drive_lh3_url

register = template.Library()

@register.simple_tag
def google_drive_image(url_or_id, alt_text="", css_class="", use_thumbnail=True, size=1200):
    """
    Template tag to display Google Drive images with fallback handling
    
    Usage:
        {% google_drive_image event.banner_image_url "Event Banner" "w-full h-48 object-cover" %}
        {% google_drive_image sponsor.logo_url "Sponsor Logo" "h-12" use_thumbnail=True size=200 %}
    """
    if not url_or_id:
        return ""
    
    # Get the file ID first
    file_id = extract_google_drive_id(url_or_id)
    if not file_id:
        return ""
    
    # Use lh3.googleusercontent.com as primary (most reliable)
    primary_url = get_google_drive_lh3_url(file_id, size)
    
    # Generate fallback URLs
    fallback_urls = [
        get_drive_image_url(url_or_id, use_thumbnail, size),
        f"https://drive.google.com/thumbnail?id={file_id}&sz=w{size}",
        f"https://drive.google.com/uc?id={file_id}"
    ]
    
    # Remove duplicates and empty URLs
    fallback_urls = [url for url in fallback_urls if url and url != primary_url]
    
    # Create img tag with multiple fallback levels
    img_html = f'<img src="{primary_url}" alt="{alt_text}" class="{css_class}" loading="lazy"'
    
    if fallback_urls:
        # Create a chain of fallbacks
        fallback_script = "this.onerror=null;"
        for i, fallback_url in enumerate(fallback_urls[:2]):  # Limit to 2 fallbacks
            fallback_script += f"this.src='{fallback_url}';this.onerror=function(){{this.onerror=null;}};"
            break  # Use only the first fallback for now
        
        img_html += f' onerror="{fallback_script}"'
    
    img_html += '>'
    
    return mark_safe(img_html)

@register.filter
def google_drive_url(url_or_id):
    """
    Filter to convert Google Drive URL or ID to direct viewable URL
    
    Usage:
        {{ event.banner_image_url|google_drive_url }}
        {{ sponsor.logo_id|google_drive_url }}
    """
    return get_drive_image_url(url_or_id)

@register.filter
def google_drive_thumbnail(url_or_id, size=400):
    """
    Filter to get Google Drive thumbnail URL
    
    Usage:
        {{ event.banner_image_url|google_drive_thumbnail:800 }}
    """
    return get_drive_image_url(url_or_id, use_thumbnail=True, size=size)

@register.filter
def extract_drive_id(url):
    """
    Filter to extract Google Drive file ID from URL
    
    Usage:
        {{ google_drive_url|extract_drive_id }}
    """
    return extract_google_drive_id(url)

@register.filter
def get_item(dictionary, key):
    """
    Filter to get an item from a dictionary by key
    
    Usage:
        {{ event_revenues|get_item:event.id }}
    """
    return dictionary.get(key) if dictionary else None

@register.filter
def multiply(value, arg):
    """Multiply value by arg."""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def split_title_main(title):
    """
    Extract the main part of event title (before ' - ' or '- ')
    
    Usage:
        {{ event.title|split_title_main }}
    """
    if ' - ' in title:
        return title.split(' - ')[0]
    elif '- ' in title:
        return title.split('- ')[0]
    return title

@register.filter
def split_title_subtitle(title):
    """
    Extract the subtitle part of event title (after ' - ' or '- ')
    
    Usage:
        {{ event.title|split_title_subtitle }}
    """
    if ' - ' in title:
        parts = title.split(' - ', 1)
        if len(parts) > 1:
            return parts[1]
    elif '- ' in title:
        parts = title.split('- ', 1)
        if len(parts) > 1:
            return parts[1]
    return ""

@register.filter
def has_dash_separator(title):
    """
    Check if title contains ' - ' or '- ' separator
    
    Usage:
        {% if event.title|has_dash_separator %}
    """
    return (' - ' in title or '- ' in title) if title else False

@register.filter
def format_event_datetime(event):
    """
    Format event date and time for display in passes and tickets
    
    Usage:
        {{ event|format_event_datetime }}
    """
    if not event or not hasattr(event, 'date') or not hasattr(event, 'time'):
        return ""
    
    try:
        date_str = event.date.strftime('%d %b %Y')
        time_str = event.time.strftime('%I:%M %p')
        return f"{date_str}, {time_str} ONWARDS"
    except (AttributeError, ValueError):
        return ""
