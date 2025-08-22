# Production Deployment Checklist

This checklist outlines essential steps for safely deploying the TapNex ticketing system to production.

## Environment Variables

Ensure the following environment variables are set in your production environment:

- `CASHFREE_CLIENT_ID`: Your production Cashfree API client ID
- `CASHFREE_CLIENT_SECRET`: Your production Cashfree API client secret
- `CASHFREE_SECRET_KEY`: Your production Cashfree webhook secret key (for signature verification)
- `CASHFREE_ENVIRONMENT`: Set to "PRODUCTION"
- `DEBUG`: Set to "False"
- `EMAIL_HOST_PASSWORD`: Gmail app password for email sending
- `SITE_DOMAIN`: Set to "https://tickets.tapnex.tech"
- `SECRET_KEY`: A strong, unique secret key for Django

## Database

- Ensure production database credentials are secure
- Run database migrations: `python manage.py migrate`
- Consider creating a database backup before deployment

## Static Files

- Run `python manage.py collectstatic`
- Verify WhiteNoise middleware is enabled
- Check that static files are serving correctly

## Cashfree Integration

1. **Update Webhook URL in Cashfree Dashboard**:
   - Log in to your Cashfree Production account
   - Go to Developer Settings > Webhooks
   - Update the webhook URL to: `https://tickets.tapnex.tech/cashfree/webhook/`
   - Set the webhook secret to match your `CASHFREE_SECRET_KEY`

2. **Test Production Payment Flow**:
   - Make a small test purchase to verify the entire payment flow
   - Check that webhooks are being received correctly
   - Verify that tickets are being created after successful payments

3. **Monitoring**:
   - Check logs for any payment processing errors
   - Monitor webhook signature verification success/failures
   - Set up alerts for payment failures

## Security

- Ensure SSL is properly configured (managed by Vercel)
- Verify CSRF settings are correct
- Check that security-related middleware is active
- Remove any debug output or test code
- Enable secure cookie settings

## Post-Deployment Verification

- Test user registration and login
- Test ticket booking flow end-to-end
- Test email delivery
- Verify mobile responsiveness
- Check admin functionality

## Rollback Plan

In case of issues:
1. Identify whether the issue is with code or configuration
2. If configuration: update environment variables
3. If code: roll back to previous working version
4. For database issues: restore from backup

## Notes for Cashfree Production Environment

- Production API endpoint is automatically used when `CASHFREE_ENVIRONMENT` is set to "PRODUCTION"
- Production webhooks use stricter validation rules - ensure your webhook handler is robust
- Monitor transaction statuses through the Cashfree merchant dashboard
