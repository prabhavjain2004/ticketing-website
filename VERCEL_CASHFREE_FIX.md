# Vercel Environment Variables Setup Guide

## The Problem
Your application works locally but fails in production because:
- **Local**: Uses SANDBOX environment with TEST credentials ✅
- **Production**: Was trying to use PRODUCTION environment with TEST credentials ❌

## Solution 1: Use SANDBOX in Production (Recommended for testing)

The `vercel.json` has been updated to use SANDBOX environment. 

You still need to set these environment variables in Vercel:

### Go to Vercel Dashboard → Your Project → Settings → Environment Variables

Add these variables:

1. **CASHFREE_CLIENT_ID**
   - Value: `[Copy from your local .env file]`

2. **CASHFREE_CLIENT_SECRET**
   - Value: `[Copy from your local .env file]`

3. **CASHFREE_ENVIRONMENT** 
   - Value: `SANDBOX`

### After adding these variables:
1. Go to Vercel → Deployments
2. Click the three dots (...) on your latest deployment
3. Click "Redeploy" to apply the new environment variables

## Solution 2: Get Production Credentials (For live payments)

If you want to accept real payments:

1. Get **PRODUCTION** credentials from Cashfree
2. Replace the TEST credentials with PRODUCTION ones in Vercel
3. Set `CASHFREE_ENVIRONMENT` to `PRODUCTION` in Vercel
4. Update `vercel.json` to use `CASHFREE_ENVIRONMENT: "PRODUCTION"`

## Testing the Fix

After redeployment, test the payment flow again. The error should be resolved.

## Debugging

The views now include debug prints that will show in Vercel logs:
- Whether credentials are configured
- Which environment is being used
- More detailed error messages

Check Vercel → Functions → View Function Logs to see these debug messages.

## Note
Copy the actual values from your local .env file when setting up Vercel environment variables.
