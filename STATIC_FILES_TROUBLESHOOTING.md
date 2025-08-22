# 🔧 Static Files Troubleshooting Guide

## 🚨 Current Issue
Images, logos, and sounds are not displaying on Vercel deployment (showing alt text/placeholders instead).

## 🔍 Diagnostic Steps

### 1. Check Static Files Collection
```bash
# Verify static files are collected
python manage.py collectstatic --noinput --clear

# Check if files exist
ls -la staticfiles_build/core/images/
ls -la staticfiles_build/sounds/
```

### 2. Test Static File URLs
Visit these URLs on your deployed site:
- `https://your-domain.vercel.app/static/core/images/TAPNEX_LOGO_BG.jpg`
- `https://your-domain.vercel.app/static/core/images/LOGO_NEXGEN_FC.png`
- `https://your-domain.vercel.app/static/sounds/SUCCESSFUL_SCAN.mp3`

### 3. Check Vercel Build Logs
Look for:
- `collectstatic` command execution
- Static files being uploaded
- Any errors during build process

## 🛠️ Solutions to Try

### Solution 1: Update Vercel Configuration
```json
{
  "version": 2,
  "builds": [
    {
      "src": "tapnex_ticketing_system/wsgi.py",
      "use": "@vercel/python",
      "config": { 
        "maxLambdaSize": "15mb"
      }
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "/staticfiles_build/static/$1"
    },
    {
      "src": "/media/(.*)",
      "dest": "/media/$1"
    },
    {
      "src": "/(.*)",
      "dest": "tapnex_ticketing_system/wsgi.py"
    }
  ],
  "env": {
    "DJANGO_SETTINGS_MODULE": "tapnex_ticketing_system.settings",
    "DEBUG": "False",
    "ALLOWED_HOSTS": "tickets.tapnex.tech,ticketing-website-o9431afou-prabhav-jains-projects.vercel.app",
    "CASHFREE_ENVIRONMENT": "PRODUCTION"
  }
}
```

### Solution 2: Alternative Static Files Approach
If the above doesn't work, try this alternative configuration:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "tapnex_ticketing_system/wsgi.py",
      "use": "@vercel/python",
      "config": { 
        "maxLambdaSize": "15mb"
      }
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "/staticfiles_build/static/$1",
      "headers": {
        "Cache-Control": "public, max-age=31536000"
      }
    },
    {
      "src": "/media/(.*)",
      "dest": "/media/$1"
    },
    {
      "src": "/(.*)",
      "dest": "tapnex_ticketing_system/wsgi.py"
    }
  ],
  "env": {
    "DJANGO_SETTINGS_MODULE": "tapnex_ticketing_system.settings",
    "DEBUG": "False",
    "ALLOWED_HOSTS": "tickets.tapnex.tech,ticketing-website-o9431afou-prabhav-jains-projects.vercel.app",
    "CASHFREE_ENVIRONMENT": "PRODUCTION"
  }
}
```

### Solution 3: Use CDN for Static Files
If Vercel static files continue to fail, consider using a CDN:

1. **Upload static files to Cloudinary or AWS S3**
2. **Update Django settings to use CDN URLs**
3. **Update templates to use CDN URLs**

### Solution 4: Manual Static File Serving
Create a custom view to serve static files:

```python
# In views.py
from django.http import FileResponse
from django.conf import settings
import os

def serve_static_file(request, file_path):
    """Serve static files manually"""
    full_path = os.path.join(settings.STATIC_ROOT, file_path)
    if os.path.exists(full_path):
        return FileResponse(open(full_path, 'rb'))
    else:
        from django.http import Http404
        raise Http404("File not found")
```

## 🔧 Manual Testing

### Test 1: Check File Existence
```bash
# Check if files exist locally
ls -la staticfiles_build/core/images/TAPNEX_LOGO_BG.jpg
ls -la staticfiles_build/sounds/SUCCESSFUL_SCAN.mp3
```

### Test 2: Check File Permissions
```bash
# Ensure files are readable
chmod 644 staticfiles_build/core/images/*
chmod 644 staticfiles_build/sounds/*
```

### Test 3: Test Direct Access
Try accessing the static files directly:
- `https://your-domain.vercel.app/static/core/images/TAPNEX_LOGO_BG.jpg`
- Should return the image, not 404

## 🚨 Emergency Solutions

### Option 1: Use Base64 Images
Convert critical images to base64 and embed them directly in CSS:

```css
.tapnex-logo {
    background-image: url('data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...');
}
```

### Option 2: Use External Image Hosting
Upload images to:
- Imgur
- Cloudinary
- AWS S3
- GitHub (raw content)

### Option 3: Use Font Icons
Replace images with font icons where possible:
- Font Awesome
- Material Icons
- Custom SVG icons

## 📞 Next Steps

1. **Try Solution 1** - Update vercel.json
2. **Deploy and test** - Check if images load
3. **If still failing** - Try Solution 2
4. **Check Vercel logs** - Look for specific errors
5. **Consider CDN** - For reliable static file hosting

## 🎯 Success Criteria

- [ ] Images load without placeholders
- [ ] Sounds play correctly
- [ ] CSS styles apply properly
- [ ] No 404 errors for static files
- [ ] Fast loading times

---

**Last Updated:** $(date)
**Status:** 🔧 Troubleshooting in progress
