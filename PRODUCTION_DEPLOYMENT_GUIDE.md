# 💰 PRODUCTION MODE DEPLOYMENT GUIDE

## ⚠️ CRITICAL: REAL MONEY TRANSACTIONS

This guide configures your application for **PRODUCTION** mode with **REAL MONEY** transactions through Cashfree.

## 🔑 Step 1: Get Production Credentials

1. **Login to Cashfree Dashboard**
   - Go to [Cashfree Dashboard](https://dashboard.cashfree.com/)
   - Switch to **Production** mode (top right toggle)

2. **Get API Credentials**
   - Go to **Developers** > **API Keys**
   - Copy your production credentials:
     - Client ID (starts with production prefix, not TEST)
     - Client Secret
     - Create a webhook secret key

## 🛠️ Step 2: Update Environment Variables

### Local Environment (.env file)
Replace the placeholder values with your actual production credentials:

```env
CASHFREE_CLIENT_ID=your_actual_production_client_id
CASHFREE_CLIENT_SECRET=your_actual_production_client_secret
CASHFREE_SECRET_KEY=your_production_webhook_secret
CASHFREE_ENVIRONMENT=PRODUCTION
```

### Vercel Environment Variables
Update these in your Vercel dashboard (Settings > Environment Variables):

- `CASHFREE_CLIENT_ID` = your production client ID
- `CASHFREE_CLIENT_SECRET` = your production client secret  
- `CASHFREE_SECRET_KEY` = your production webhook secret
- `CASHFREE_ENVIRONMENT` = `PRODUCTION`

## 🔗 Step 3: Configure Webhooks

1. **In Cashfree Production Dashboard**
   - Go to **Developers** > **Webhooks**
   - Add webhook URL: `https://tickets.tapnex.tech/cashfree-webhook/`
   - Select events:
     - `PAYMENT_SUCCESS_WEBHOOK`
     - `PAYMENT_FAILED_WEBHOOK` 
     - `PAYMENT_USER_DROPPED_WEBHOOK`
   - Use the same secret key as `CASHFREE_SECRET_KEY`

## ✅ Step 4: Verification

Run the production verification script:
```bash
python verify_production_setup.py
```

## 🚀 Step 5: Deploy

```bash
# Commit changes
git add .
git commit -m "Configure for production Cashfree integration"

# Deploy to Vercel
git push origin master
```

## 🧪 Step 6: Production Testing Protocol

### Phase 1: Small Amount Testing
1. **Start with ₹1-10 transactions**
2. **Test all payment methods:**
   - Credit/Debit Cards
   - UPI
   - Net Banking
   - Wallets

### Phase 2: User Journey Testing
1. **Complete booking flow**
2. **Verify email notifications**
3. **Check ticket generation**
4. **Test QR code scanning**

## 🚨 PRODUCTION SAFETY CHECKLIST

### Before Going Live:
- [ ] Production credentials configured
- [ ] Webhooks tested and working
- [ ] Small amount transactions successful
- [ ] Email notifications working
- [ ] Refund process tested

### After Going Live:
- [ ] Monitor transactions daily
- [ ] Set up payment alerts
- [ ] Regular webhook health checks
- [ ] Customer support process ready

---

**🎯 YOU ARE NOW IN PRODUCTION MODE - REAL MONEY TRANSACTIONS** 💰
