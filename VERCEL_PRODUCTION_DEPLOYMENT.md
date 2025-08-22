# Vercel Production Deployment Checklist

This checklist outlines the steps to deploy your Django application to Vercel with Cashfree payments in production mode.

## Before Deployment

1. **Environment Variables**
   - [ ] Add all required environment variables in Vercel project settings:
     - `CASHFREE_CLIENT_ID` (production)
     - `CASHFREE_CLIENT_SECRET` (production)
     - `CASHFREE_SECRET_KEY` (production)
     - `CASHFREE_ENVIRONMENT=PRODUCTION`
     - `DEBUG=False`
     - `EMAIL_HOST_PASSWORD`
     - `SECRET_KEY`
     - Any other environment-specific variables

2. **Static Files**
   - [ ] Make sure `vercel.json` includes the correct static file handling
   - [ ] Run `python manage.py collectstatic` locally and commit the `staticfiles_build` directory

3. **Database Configuration**
   - [ ] Ensure your database configuration is correct
   - [ ] Run migrations locally to verify schema

## Deployment Process

1. **Push to GitHub Repository**
   ```bash
   git add .
   git commit -m "Prepare for production deployment"
   git push origin master
   ```

2. **Deploy on Vercel**
   - [ ] Go to Vercel dashboard and deploy from your GitHub repository
   - [ ] Ensure that all environment variables are correctly set in Vercel

## Post-Deployment Checks

1. **Basic Functionality**
   - [ ] Visit the site and verify it loads correctly
   - [ ] Check that static files (CSS, JS, images) load properly
   - [ ] Test user registration/login

2. **Cashfree Integration**
   - [ ] Configure webhooks in Cashfree dashboard to point to your production URL
   - [ ] Make a test purchase with a small amount
   - [ ] Verify webhook delivery and signature validation
   - [ ] Check that tickets are correctly created after payment

3. **Error Handling**
   - [ ] Verify that 404, 500, and other error pages display correctly
   - [ ] Check logging functionality is working

## Monitoring

1. **Set Up Logging**
   - [ ] Configure error reporting in Vercel
   - [ ] Set up email notifications for critical errors

2. **Analytics**
   - [ ] Set up analytics to track usage and conversions

## Rollback Plan

If issues arise:
1. Roll back to previous version in Vercel dashboard
2. Check logs to identify the specific problem
3. Fix issues locally and redeploy

## DNS Configuration

1. **Custom Domain**
   - [ ] Add your custom domain in Vercel (e.g., tickets.tapnex.tech)
   - [ ] Configure DNS records as per Vercel instructions
   - [ ] Ensure HTTPS is properly configured

## Cashfree Dashboard Final Setup

1. **Production Credentials**
   - [ ] Ensure you're using production credentials, not test/sandbox
   - [ ] Verify webhook URL is updated to your production domain
   - [ ] Test all payment flows end-to-end
