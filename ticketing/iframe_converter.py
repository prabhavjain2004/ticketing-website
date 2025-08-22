"""
Google Drive iframe to img tag converter utility

This utility converts Google Drive iframe preview codes to proper HTML img tags
for use in web applications.

Example usage:
    iframe_code = '<iframe src="https://drive.google.com/file/d/1nu-W80HaCOhyw_UcEP_I55tTJuv2gNic/preview" width="640" height="480" allow="autoplay"></iframe>'
    img_tag = convert_iframe_to_img_tag(iframe_code, "tapnex logo")
    # Returns: <img src="https://drive.google.com/uc?export=view&id=1nu-W80HaCOhyw_UcEP_I55tTJuv2gNic" alt="tapnex logo">
"""

import re
from typing import Optional


def convert_iframe_to_img_tag(iframe_code: str, alt_text: str = "", css_class: str = "") -> str:
    """
    Convert Google Drive iframe preview code to HTML img tag
    
    Args:
        iframe_code: The iframe HTML code from Google Drive
        alt_text: Alt text for the image (defaults to empty string)
        css_class: CSS classes to apply to the img tag (defaults to empty string)
        
    Returns:
        HTML img tag with proper Google Drive direct URL
        
    Example:
        >>> iframe = '<iframe src="https://drive.google.com/file/d/1nu-W80HaCOhyw_UcEP_I55tTJuv2gNic/preview" width="640" height="480"></iframe>'
        >>> convert_iframe_to_img_tag(iframe, "tapnex logo")
        '<img src="https://drive.google.com/uc?export=view&id=1nu-W80HaCOhyw_UcEP_I55tTJuv2gNic" alt="tapnex logo">'
    """
    # Extract the source URL from the iframe
    iframe_match = re.search(r'<iframe[^>]*src="([^"]*)"[^>]*>', iframe_code, re.IGNORECASE)
    
    if not iframe_match:
        return ""
    
    src_url = iframe_match.group(1)
    
    # Extract the file ID from the URL
    file_id = extract_file_id_from_url(src_url)
    
    if not file_id:
        return ""
    
    # Create the direct view URL
    direct_url = f"https://drive.google.com/uc?export=view&id={file_id}"
    
    # Build the img tag
    img_parts = [f'<img src="{direct_url}"']
    
    if alt_text:
        img_parts.append(f'alt="{alt_text}"')
    
    if css_class:
        img_parts.append(f'class="{css_class}"')
    
    return f"{' '.join(img_parts)}>"


def extract_file_id_from_url(url: str) -> Optional[str]:
    """
    Extract Google Drive file ID from URL
    
    Args:
        url: Google Drive URL
        
    Returns:
        File ID if found, None otherwise
    """
    patterns = [
        r'/d/([a-zA-Z0-9-_]+)',  # /file/d/FILE_ID/preview or /view
        r'id=([a-zA-Z0-9-_]+)',  # ?id=FILE_ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def process_admin_input(input_data: str, description: str = "") -> dict:
    """
    Process admin input (either iframe or URL) and return structured data
    
    Args:
        input_data: Either iframe code or Google Drive URL
        description: Description for the image
        
    Returns:
        Dictionary containing:
        - file_id: Extracted Google Drive file ID
        - direct_url: Direct viewable URL
        - img_tag: Ready-to-use img tag
        - is_iframe: Whether input was iframe code
    """
    # Check if input is an iframe
    is_iframe = bool(re.search(r'<iframe[^>]*>', input_data, re.IGNORECASE))
    
    if is_iframe:
        # Extract file ID from iframe
        iframe_match = re.search(r'<iframe[^>]*src="([^"]*)"[^>]*>', input_data, re.IGNORECASE)
        if iframe_match:
            file_id = extract_file_id_from_url(iframe_match.group(1))
        else:
            file_id = None
    else:
        # Extract file ID directly from URL
        file_id = extract_file_id_from_url(input_data)
    
    if not file_id:
        return {
            'file_id': None,
            'direct_url': None,
            'img_tag': None,
            'is_iframe': is_iframe,
            'error': 'Could not extract file ID from input'
        }
    
    direct_url = f"https://drive.google.com/uc?export=view&id={file_id}"
    img_tag = f'<img src="{direct_url}" alt="{description}">'
    
    return {
        'file_id': file_id,
        'direct_url': direct_url,
        'img_tag': img_tag,
        'is_iframe': is_iframe,
        'error': None
    }


# Example usage and testing
if __name__ == "__main__":
    # Test with iframe
    iframe_example = '<iframe src="https://drive.google.com/file/d/1nu-W80HaCOhyw_UcEP_I55tTJuv2gNic/preview" width="640" height="480" allow="autoplay"></iframe>'
    result = convert_iframe_to_img_tag(iframe_example, "tapnex logo")
    print("Iframe conversion result:")
    print(result)
    
    # Test with URL
    url_example = "https://drive.google.com/file/d/1nu-W80HaCOhyw_UcEP_I55tTJuv2gNic/view"
    result2 = process_admin_input(url_example, "tapnex logo")
    print("\nURL processing result:")
    print(result2)
    
    # Test with iframe processing
    result3 = process_admin_input(iframe_example, "tapnex logo")
    print("\nIframe processing result:")
    print(result3)
