# 🚀 Vercel Deployment Guide for TapNex

## 🎯 Overview
This guide will help you properly deploy your Django application to Vercel with working static files.

## 📋 Prerequisites
- Vercel CLI installed: `npm i -g vercel`
- Git repository connected to Vercel
- All static files properly collected

## 🔧 Step-by-Step Deployment

### 1. Prepare Your Project
```bash
# Ensure static files are collected
python manage.py collectstatic --noinput --clear

# Verify static files exist
ls -la staticfiles_build/core/images/
ls -la staticfiles_build/sounds/
```

### 2. Deploy to Vercel
```bash
# Deploy to production
vercel --prod

# Or for preview
vercel
```

### 3. Set Environment Variables in Vercel Dashboard
Go to your Vercel project dashboard and set these environment variables:

**Required Variables:**
- `DJANGO_SETTINGS_MODULE`: `tapnex_ticketing_system.settings`
- `DEBUG`: `False`
- `ALLOWED_HOSTS`: `tickets.tapnex.tech,ticketing-website-o9431afou-prabhav-jains-projects.vercel.app`
- `CASHFREE_ENVIRONMENT`: `PRODUCTION`

**Database Variables:**
- `DATABASE_URL`: Your Supabase PostgreSQL connection string

**Email Variables:**
- `EMAIL_HOST_PASSWORD`: Your Gmail app password

**Cashfree Variables:**
- `CASHFREE_CLIENT_ID`: Your Cashfree client ID
- `CASHFREE_CLIENT_SECRET`: Your Cashfree client secret

### 4. Test Your Deployment
Visit these URLs to verify everything works:
- Main site: `https://your-domain.vercel.app`
- Static files test: `https://your-domain.vercel.app/test-static/`
- Admin panel: `https://your-domain.vercel.app/admin/`

## 🔍 Troubleshooting

### If Static Files Don't Load:
1. **Check Vercel Build Logs**
   - Look for `collectstatic` errors
   - Verify static files are being uploaded

2. **Verify Static Files Route**
   - Test: `https://your-domain.vercel.app/static/core/images/TAPNEX_LOGO_BG.jpg`
   - Should return the image, not 404

3. **Check Environment Variables**
   - Ensure `DEBUG=False` is set
   - Verify `ALLOWED_HOSTS` includes your domain

### If App Doesn't Deploy:
1. **Check Python Version**
   - Vercel supports Python 3.9+
   - Ensure compatibility

2. **Check Dependencies**
   - All packages in `requirements.txt` must be compatible
   - Some packages might need specific versions

3. **Check File Size Limits**
   - Vercel has 15MB function size limit
   - Large static files might cause issues

## 📁 File Structure for Vercel
```
your-project/
├── vercel.json              # Vercel configuration
├── requirements.txt          # Python dependencies
├── manage.py                # Django management
├── tapnex_ticketing_system/
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URLs
│   └── wsgi.py              # WSGI application
├── ticketing/               # Your Django app
├── staticfiles_build/       # Collected static files
└── templates/               # HTML templates
```

## 🔧 Configuration Files

### vercel.json
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
  },
  "functions": {
    "tapnex_ticketing_system/wsgi.py": {
      "maxDuration": 30
    }
  }
}
```

## 🚨 Common Issues & Solutions

### Issue: Static Files 404
**Solution:**
1. Ensure `collectstatic` runs during build
2. Check static files route in `vercel.json`
3. Verify files exist in `staticfiles_build/`

### Issue: Database Connection Failed
**Solution:**
1. Set `DATABASE_URL` in Vercel environment variables
2. Ensure database allows external connections
3. Check network security groups

### Issue: App Times Out
**Solution:**
1. Increase `maxDuration` in `vercel.json`
2. Optimize database queries
3. Use caching where possible

### Issue: Environment Variables Not Working
**Solution:**
1. Redeploy after setting environment variables
2. Check variable names match exactly
3. Restart the function

## 📞 Support

If you encounter issues:
1. Check Vercel build logs
2. Visit `/test-static/` for diagnostics
3. Review this guide
4. Check Vercel documentation

## 🎉 Success Checklist

- [ ] App deploys without errors
- [ ] Static files load correctly
- [ ] Database connections work
- [ ] Admin panel accessible
- [ ] Email functionality works
- [ ] Payment processing works
- [ ] All images and sounds display

---

**Last Updated:** $(date)
**Status:** ✅ Ready for deployment
