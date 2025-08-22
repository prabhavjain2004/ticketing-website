# TEST MODE DEPLOYMENT CHECKLIST

## ✅ Current Status: CONFIGURED FOR TEST MODE

Your application is now properly configured to run in test/sandbox mode with the following setup:

### 🔧 Configuration Changes Made

1. **Vercel Configuration (`vercel.json`)**
   - ✅ Set `CASHFREE_ENVIRONMENT=SANDBOX`
   - ✅ Maintains `DEBUG=False` for production-like environment

2. **Django Settings (`settings.py`)**
   - ✅ Default Cashfree environment changed to SANDBOX
   - ✅ Database configuration uses environment variables
   - ✅ Secret key uses environment variable
   - ✅ Email configuration uses environment variables

3. **Environment Variables (`.env`)**
   - ✅ `CASHFREE_ENVIRONMENT=SANDBOX`
   - ✅ Using TEST Cashfree credentials
   - ✅ All required environment variables configured

### 🚀 Deployment Steps

1. **Verify Local Configuration**
   ```bash
   python verify_test_setup.py
   ```

2. **Update Vercel Environment Variables**
   - Go to your Vercel dashboard
   - Navigate to your project settings
   - Update the following environment variables:
     - `CASHFREE_CLIENT_ID` = `your_test_client_id_from_cashfree`
     - `CASHFREE_CLIENT_SECRET` = `your_test_client_secret_from_cashfree`
     - `CASHFREE_SECRET_KEY` = `your_test_webhook_secret_key`
     - `CASHFREE_ENVIRONMENT` = `SANDBOX`
     - `EMAIL_HOST_PASSWORD` = `your_gmail_app_password`
     - `SECRET_KEY` = `your_django_secret_key`
     - `SUPABASE_DB_NAME` = `postgres`
     - `SUPABASE_DB_USER` = `your_supabase_user`
     - `SUPABASE_DB_PASSWORD` = `your_supabase_password`
     - `SUPABASE_DB_HOST` = `your_supabase_host`
     - `SUPABASE_DB_PORT` = `6543`

3. **Deploy to Vercel**
   ```bash
   git add .
   git commit -m "Configure for test mode deployment"
   git push origin master
   ```

4. **Verify Deployment**
   - Check Vercel deployment logs
   - Test your website functionality
   - Verify Cashfree payments are processed in sandbox

### 🧪 Testing Checklist

After deployment, test the following:

- [ ] **Website loads correctly**
  - [ ] Home page displays
  - [ ] Static files load (CSS, JS, images)
  - [ ] Event pages are accessible

- [ ] **User Authentication**
  - [ ] User registration works
  - [ ] User login works
  - [ ] Password reset works

- [ ] **Event Booking Flow**
  - [ ] Browse events
  - [ ] Select event and proceed to booking
  - [ ] Fill booking form
  - [ ] Proceed to payment

- [ ] **Cashfree Payment Testing**
  - [ ] Payment page loads
  - [ ] Test payment with sandbox credentials
  - [ ] Payment success redirects correctly
  - [ ] Booking confirmation email sent
  - [ ] Ticket generated successfully

- [ ] **Admin Functions**
  - [ ] Admin login works
  - [ ] Event management
  - [ ] User management
  - [ ] View bookings and payments

### 🔍 Cashfree Sandbox Testing

Use these test payment details in sandbox mode:

**Test Card Numbers:**
- **Success:** 4111 1111 1111 1111
- **Failure:** 4111 1111 1111 1112

**Test UPI:**
- **Success:** success@payu
- **Failure:** failure@payu

**Test Net Banking:**
- Use any test bank provided in the Cashfree sandbox

### 📋 Verification Commands

Run these commands to verify your setup:

```bash
# Check test configuration
python verify_test_setup.py

# Test Cashfree order creation
python test_create_order_function.py

# Check for any configuration issues
python check_cashfree_config.py
```

### 🚨 Important Notes

1. **Sandbox Mode**: All payments will be processed in Cashfree's sandbox environment
2. **Test Credentials**: Currently using TEST API keys - no real money will be charged
3. **Email Testing**: Emails will be sent but are for testing purposes
4. **Database**: Using production Supabase database - test data will be mixed with any existing data

### 🎯 When Ready for Production

When you're ready to go live:

1. **Get Production API Keys**
   - Login to Cashfree dashboard
   - Switch to Production mode
   - Get production API credentials

2. **Update Environment Variables**
   - Replace TEST credentials with production credentials
   - Change `CASHFREE_ENVIRONMENT` to `PRODUCTION`

3. **Update Webhook URLs**
   - Configure webhook URLs in Cashfree dashboard to point to your production domain

4. **Security Review**
   - Ensure all sensitive data is properly secured
   - Review ALLOWED_HOSTS settings
   - Consider enabling additional security headers

---

**🎉 Your test environment is now ready! Deploy to Vercel and start testing your payment flow.**
