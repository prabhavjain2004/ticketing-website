# Cashfree Production Setup Guide

This guide outlines the process of configuring Cashfree Payments for the production environment.

## 1. Update Environment Variables

Update your `.env` file with the following production values:

```
CASHFREE_CLIENT_ID=your_production_client_id
CASHFREE_CLIENT_SECRET=your_production_client_secret
CASHFREE_SECRET_KEY=your_production_webhook_secret
CASHFREE_ENVIRONMENT=PRODUCTION
```

**Note**: The `CASHFREE_SECRET_KEY` is different from your `CASHFREE_CLIENT_SECRET`. It's used specifically for verifying webhook signatures.

## 2. Configure Webhook in Cashfree Dashboard

1. Log in to your [Cashfree Production Dashboard](https://merchant.cashfree.com/login)
2. Navigate to Settings > Webhooks
3. Add a new webhook with the URL: `https://tickets.tapnex.tech/cashfree/webhook/`
4. Set the webhook secret to match your `CASHFREE_SECRET_KEY` value
5. Enable the following events:
   - Payment Success
   - Payment Failure
   - Payment Expiry/Cancellation

## 3. Configure Payment Success Redirect URL

For production payments, ensure your checkout configuration uses the correct production domain:

```
return_url = request.build_absolute_uri(reverse('payment_status')) + 
            f"?order_id={{order_id}}&session_order_id={order_id}&" + 
            f"payment_status={{payment_status}}&transaction_id={{transaction_id}}"
```

This is already handled in the code by using `request.build_absolute_uri()` which builds URLs based on the current domain.

## 4. Testing Production Integration

After switching to production, perform these tests:

1. Make a small test purchase to verify the full payment flow
2. Check logs to ensure webhooks are being received and validated
3. Verify that tickets are generated after successful payment
4. Test refund flow if applicable

## 5. Common Production Issues

### Webhook Signature Verification Failures

If webhook verification fails:
- Check that `CASHFREE_SECRET_KEY` matches exactly with the secret in Cashfree dashboard
- Verify that webhook URL is correctly configured
- Check for any proxy/load balancer issues that might modify request headers

### Payment Creation Failures

If payment creation fails:
- Verify `CASHFREE_CLIENT_ID` and `CASHFREE_CLIENT_SECRET` are correct
- Check logs for any API response errors
- Ensure your Cashfree account is fully activated for production

## 6. Production Support

For production issues with Cashfree:
- Support email: care@cashfree.com
- Support phone: 1800-419-5104
- Dashboard: https://merchant.cashfree.com/

## 7. Monitoring

Monitor the following metrics:
- Payment success rate
- Webhook delivery success rate
- Order creation success rate
- Average payment processing time

## 8. Important Notes

- Production transactions involve real money - be careful with testing
- Cashfree production webhooks are only sent to HTTPS URLs
- Keep your production credentials secure and never commit them to code repositories
- Different error codes may appear in production vs. sandbox environment
