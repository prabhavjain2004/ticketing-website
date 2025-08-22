"""
Test script to verify iframe processing works correctly
"""

import sys
import os
import re

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Import the Google Drive utilities
from ticketing.google_drive_utils import extract_google_drive_id, is_valid_google_drive_url

def test_iframe_processing():
    """Test iframe processing functionality"""
    
    # Test iframe code from your example
    iframe_code = '<iframe src="https://drive.google.com/file/d/1nu-W80HaCOhyw_UcEP_I55tTJuv2gNic/preview" width="640" height="480" allow="autoplay"></iframe>'
    
    print("🧪 Testing iframe processing...")
    print(f"Input iframe: {iframe_code}")
    
    # Test file ID extraction
    file_id = extract_google_drive_id(iframe_code)
    print(f"Extracted file ID: {file_id}")
    
    # Test validation
    is_valid = is_valid_google_drive_url(iframe_code)
    print(f"Is valid: {is_valid}")
    
    # Test regular URL as well
    regular_url = "https://drive.google.com/file/d/1nu-W80HaCOhyw_UcEP_I55tTJuv2gNic/view"
    file_id_2 = extract_google_drive_id(regular_url)
    is_valid_2 = is_valid_google_drive_url(regular_url)
    
    print(f"\n🔗 Testing regular URL: {regular_url}")
    print(f"Extracted file ID: {file_id_2}")
    print(f"Is valid: {is_valid_2}")
    
    # Verify both methods extract the same file ID
    if file_id == file_id_2:
        print(f"\n✅ SUCCESS: Both methods extract the same file ID: {file_id}")
        
        # Generate direct URL
        direct_url = f"https://drive.google.com/uc?export=view&id={file_id}"
        print(f"Direct URL: {direct_url}")
        
        # Generate img tag
        img_tag = f'<img src="{direct_url}" alt="tapnex logo">'
        print(f"Generated img tag: {img_tag}")
        
        return True
    else:
        print(f"\n❌ ERROR: File IDs don't match!")
        print(f"Iframe ID: {file_id}")
        print(f"URL ID: {file_id_2}")
        return False

if __name__ == "__main__":
    success = test_iframe_processing()
    if success:
        print("\n🎉 All tests passed! Iframe processing is working correctly.")
    else:
        print("\n💥 Tests failed! Check the implementation.")
