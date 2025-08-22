# Google Drive Iframe Support Implementation

## Overview
Enhanced the existing Google Drive image processing system to accept iframe preview codes in addition to regular Google Drive URLs. This allows admins to paste iframe codes directly from Google Drive's preview/embed functionality.

## Key Features Implemented

### 1. Iframe Code Processing
- **Input**: `<iframe src="https://drive.google.com/file/d/1nu-W80HaCOhyw_UcEP_I55tTJuv2gNic/preview" width="640" height="480" allow="autoplay"></iframe>`
- **Output**: `<img src="https://drive.google.com/uc?export=view&id=1nu-W80HaCOhyw_UcEP_I55tTJuv2gNic" alt="description">`

### 2. Enhanced Validation
- Updated `extract_google_drive_id()` to handle iframe src extraction
- Enhanced `is_valid_google_drive_url()` to validate iframe codes
- Added iframe pattern matching in form validation

### 3. Form Updates
- Changed input type from `URLInput` to `TextInput` to accept multi-line iframe codes
- Updated placeholders to indicate iframe support
- Enhanced help text to explain both URL and iframe options
- Updated validation error messages

### 4. JavaScript Enhancement
- Updated `extractGoogleDriveId()` function to handle iframe extraction
- Maintained backward compatibility with existing URL formats

## Files Modified

### Core Utilities
1. **`ticketing/google_drive_utils.py`**
   - Enhanced `extract_google_drive_id()` with iframe pattern
   - Updated `is_valid_google_drive_url()` for iframe validation

2. **`ticketing/iframe_converter.py`** (New)
   - Standalone utility for iframe to img tag conversion
   - Example usage and testing functions

### Forms
3. **`ticketing/forms.py`**
   - Updated `EventForm.banner_image_url` widget to TextInput
   - Enhanced `clean_banner_image_url()` validation
   - Updated `EventSponsorForm.logo_url` widget and validation
   - Added iframe processing logic in form validation

### Templates
4. **`ticketing/templates/core/admin/event_form.html`**
   - Updated JavaScript `extractGoogleDriveId()` function
   - Enhanced help documentation with iframe examples
   - Updated step-by-step guide

### Documentation
5. **`ticketing/static/core/docs/google_drive_integration_guide.md`**
   - Added iframe support documentation
   - Included conversion examples

## How It Works

### Process Flow
1. **Admin Input**: Admin pastes either a Google Drive URL or iframe code
2. **Validation**: Form validates the input (URL or iframe)
3. **ID Extraction**: System extracts file ID from either format
4. **Storage**: Original input stored in URL field, file ID in separate field
5. **Display**: Template tags convert to proper `<img>` tags for rendering

### Conversion Logic
```python
# Input iframe
iframe = '<iframe src="https://drive.google.com/file/d/FILE_ID/preview" ...></iframe>'

# Extract src URL
src_url = "https://drive.google.com/file/d/FILE_ID/preview"

# Extract file ID
file_id = "FILE_ID"

# Generate direct URL
direct_url = "https://drive.google.com/uc?export=view&id=FILE_ID"

# Create img tag
img_tag = '<img src="direct_url" alt="description">'
```

### Supported Input Formats
- Regular URLs: `https://drive.google.com/file/d/FILE_ID/view`
- Share URLs: `https://drive.google.com/open?id=FILE_ID`
- Iframe codes: `<iframe src="https://drive.google.com/file/d/FILE_ID/preview" ...></iframe>`

## Benefits

1. **Improved User Experience**: Admins can paste iframe codes directly from Google Drive
2. **Flexibility**: Supports multiple input formats
3. **Backward Compatibility**: Existing URL inputs continue to work
4. **Automatic Processing**: System handles conversion automatically
5. **Consistent Output**: All formats result in proper `<img>` tags

## Usage Examples

### For Event Banners
```html
<!-- Admin can paste either: -->
https://drive.google.com/file/d/1nu-W80HaCOhyw_UcEP_I55tTJuv2gNic/view

<!-- OR -->
<iframe src="https://drive.google.com/file/d/1nu-W80HaCOhyw_UcEP_I55tTJuv2gNic/preview" width="640" height="480" allow="autoplay"></iframe>

<!-- Both result in: -->
{% google_drive_image event.banner_image_url event.title "w-full h-64 object-cover" %}
```

### For Sponsor Logos
```html
<!-- Same flexibility for sponsor logos -->
<iframe src="https://drive.google.com/file/d/SPONSOR_FILE_ID/preview" ...></iframe>

<!-- Results in: -->
{% google_drive_image sponsor.logo_url sponsor.sponsor_name "h-16 w-auto mx-auto object-contain" %}
```

## Testing

The iframe converter utility includes test functions to verify:
- Iframe parsing accuracy
- File ID extraction
- Direct URL generation
- Img tag creation

Run tests with:
```bash
python ticketing/iframe_converter.py
```

## Implementation Summary

This enhancement maintains the existing robust Google Drive integration while adding support for iframe codes, making the system more flexible and user-friendly for administrators who prefer to use Google Drive's embed/preview functionality.
