"""
Google Drive utility functions for handling image URLs and file IDs
"""
import re
from typing import Optional


def extract_google_drive_id(url: str) -> str:
    """
    Extract Google Drive file ID from various URL formats including iframe preview links
    
    Args:
        url: Google Drive URL in various formats or iframe code
        
    Returns:
        Extracted file ID or empty string if not found
        
    Examples:
        >>> extract_google_drive_id('https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view')
        '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
        
        >>> extract_google_drive_id('<iframe src="https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/preview">')
        '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
    """
    if not url:
        return ''
    
    # Pattern for various Google Drive URL formats including iframe previews
    patterns = [
        r'/d/([a-zA-Z0-9-_]+)',  # https://drive.google.com/file/d/FILE_ID/view or /preview
        r'id=([a-zA-Z0-9-_]+)',  # https://drive.google.com/open?id=FILE_ID
        r'export=download&id=([a-zA-Z0-9-_]+)',  # Direct download links
        r'/d/([a-zA-Z0-9-_]+)/edit',  # Edit links
        r'spreadsheets/d/([a-zA-Z0-9-_]+)',  # Google Sheets
        r'document/d/([a-zA-Z0-9-_]+)',  # Google Docs
        r'presentation/d/([a-zA-Z0-9-_]+)',  # Google Slides
        r'src="[^"]*\/d\/([a-zA-Z0-9-_]+)',  # iframe src links
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return ''


def get_google_drive_direct_url(file_id: str) -> str:
    """
    Convert Google Drive file ID to direct viewable URL
    
    Args:
        file_id: Google Drive file ID
        
    Returns:
        Direct URL for displaying the image
    """
    if not file_id:
        return ''
    return f"https://drive.google.com/uc?id={file_id}"


def get_google_drive_thumbnail_url(file_id: str, size: int = 800) -> str:
    """
    Get thumbnail URL for Google Drive image
    
    Args:
        file_id: Google Drive file ID
        size: Thumbnail size (width in pixels)
        
    Returns:
        Thumbnail URL
    """
    if not file_id:
        return ''
    return f"https://drive.google.com/thumbnail?id={file_id}&sz=w{size}"


def get_google_drive_lh3_url(file_id: str, size: int = 800) -> str:
    """
    Get lh3.googleusercontent.com direct URL for Google Drive image
    This is often more reliable than other formats
    
    Args:
        file_id: Google Drive file ID
        size: Image width in pixels
        
    Returns:
        Direct lh3.googleusercontent.com URL
    """
    if not file_id:
        return ''
    return f"https://lh3.googleusercontent.com/d/{file_id}=w{size}"


def is_valid_google_drive_url(url: str) -> bool:
    """
    Check if URL is a valid Google Drive link or iframe code
    
    Args:
        url: URL or iframe code to validate
        
    Returns:
        True if valid Google Drive URL or iframe, False otherwise
    """
    if not url:
        return False
    
    patterns = [
        r'drive\.google\.com/file/d/[a-zA-Z0-9-_]+',
        r'drive\.google\.com/open\?id=[a-zA-Z0-9-_]+',
        r'docs\.google\.com/.*[?&]id=[a-zA-Z0-9-_]+',
        r'drive\.google\.com/.*[?&]id=[a-zA-Z0-9-_]+',
        r'<iframe[^>]*src="[^"]*drive\.google\.com[^"]*"[^>]*>',  # iframe pattern
    ]
    
    return any(re.search(pattern, url) for pattern in patterns)


def convert_sharing_url_to_direct(url: str) -> str:
    """
    Convert Google Drive sharing URL to direct viewable URL
    
    Args:
        url: Google Drive sharing URL
        
    Returns:
        Direct viewable URL or original URL if conversion fails
    """
    file_id = extract_google_drive_id(url)
    if file_id:
        return get_google_drive_direct_url(file_id)
    return url


def get_google_drive_preview_url(file_id: str) -> str:
    """
    Get preview URL for Google Drive file (works for images, docs, etc.)
    
    Args:
        file_id: Google Drive file ID
        
    Returns:
        Preview URL
    """
    if not file_id:
        return ''
    return f"https://drive.google.com/file/d/{file_id}/preview"


def validate_and_extract_drive_info(url: str) -> dict:
    """
    Validate Google Drive URL and extract useful information
    
    Args:
        url: Google Drive URL
        
    Returns:
        Dictionary with validation result and extracted information
    """
    result = {
        'is_valid': False,
        'file_id': '',
        'direct_url': '',
        'thumbnail_url': '',
        'preview_url': '',
        'error_message': ''
    }
    
    if not url:
        result['error_message'] = 'URL is required'
        return result
    
    if not is_valid_google_drive_url(url):
        result['error_message'] = 'Invalid Google Drive URL format'
        return result
    
    file_id = extract_google_drive_id(url)
    if not file_id:
        result['error_message'] = 'Could not extract file ID from URL'
        return result
    
    result.update({
        'is_valid': True,
        'file_id': file_id,
        'direct_url': get_google_drive_direct_url(file_id),
        'thumbnail_url': get_google_drive_thumbnail_url(file_id),
        'preview_url': get_google_drive_preview_url(file_id),
    })
    
    return result


# Template tags helper functions
def get_drive_image_url(url_or_id: str, use_thumbnail: bool = True, size: int = 800) -> str:
    """
    Helper function for templates to get the appropriate Google Drive image URL
    
    Args:
        url_or_id: Either a Google Drive URL or file ID
        use_thumbnail: Whether to use thumbnail URL (default True for better reliability)
        size: Thumbnail size if use_thumbnail is True
        
    Returns:
        Appropriate image URL
    """
    # Check if it's already a file ID (no slashes or domain)
    if url_or_id and '/' not in url_or_id and '.' not in url_or_id:
        file_id = url_or_id
    else:
        file_id = extract_google_drive_id(url_or_id)
    
    if not file_id:
        return ''
    
    if use_thumbnail:
        return get_google_drive_thumbnail_url(file_id, size)
    else:
        return get_google_drive_direct_url(file_id)
