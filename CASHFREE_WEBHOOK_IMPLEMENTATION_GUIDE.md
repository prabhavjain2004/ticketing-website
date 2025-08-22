# Cashfree Webhook Integration Guide

## Overview

This guide explains the correct implementation of Cashfree webhook verification. **Important: Cashfree does NOT provide a separate webhook secret key.** Webhook signature verification uses the API Secret (Client Secret) from your Cashfree dashboard.

## Key Points

- ✅ **Use API Secret for webhook verification** - There is no separate webhook secret in Cashfree
- ✅ **Signature algorithm**: HMAC SHA-256 of (timestamp + raw_payload) using API Secret
- ✅ **Encoding**: Base64 encode the resulting hash
- ✅ **Headers**: Extract `x-webhook-signature` and `x-webhook-timestamp` from request headers

## Implementation Details

### 1. Configuration (settings.py)

```python
# Only need these two keys for Cashfree integration
CASHFREE_CLIENT_ID = os.getenv('CASHFREE_CLIENT_ID')
CASHFREE_CLIENT_SECRET = os.getenv('CASHFREE_CLIENT_SECRET')  # Used for both API calls and webhook verification
CASHFREE_ENVIRONMENT = os.getenv('CASHFREE_ENVIRONMENT', 'PRODUCTION')
```

### 2. Environment Variables (.env)

```bash
CASHFREE_CLIENT_ID=your_client_id_here
CASHFREE_CLIENT_SECRET=your_client_secret_here
CASHFREE_ENVIRONMENT=PRODUCTION
```

### 3. Webhook Verification Function

```python
def verify_cashfree_signature(payload, signature, timestamp):
    """
    Verifies the webhook signature received from Cashfree to ensure authenticity.
    Uses the API Secret (Client Secret) as per Cashfree's webhook verification process.
    """
    if not signature or not timestamp:
        logger.warning("Webhook signature verification failed: Missing signature or timestamp")
        return False
    
    # Use the API Secret (Client Secret) for webhook verification as per Cashfree documentation
    secret_key = getattr(settings, 'CASHFREE_CLIENT_SECRET', None)
    if not secret_key:
        logger.error("Webhook signature verification failed: CASHFREE_CLIENT_SECRET not configured")
        return False
    
    # Cashfree webhook signature format: HMAC SHA-256 of (timestamp + payload) using API Secret
    message = timestamp + payload
    secret_bytes = secret_key.encode('utf-8')
    message_bytes = message.encode('utf-8')
    hash_obj = hmac.new(secret_bytes, msg=message_bytes, digestmod=hashlib.sha256)
    expected_signature = base64.b64encode(hash_obj.digest()).decode('utf-8')
    
    is_valid = hmac.compare_digest(expected_signature, signature)
    if not is_valid:
        logger.warning(f"Webhook signature verification failed: Expected {expected_signature}, got {signature}")
    
    return is_valid
```

### 4. Webhook Handler

```python
@csrf_exempt
def cashfree_webhook(request):
    """
    Handles incoming webhook notifications from Cashfree Payments.
    """
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)
    
    raw_payload = request.body.decode('utf-8')
    signature = request.headers.get('x-webhook-signature')
    timestamp = request.headers.get('x-webhook-timestamp')
    
    # Verify the webhook signature
    if not verify_cashfree_signature(raw_payload, signature, timestamp):
        logger.error("Webhook signature verification failed")
        return HttpResponse("Unauthorized", status=401)
    
    # Process the webhook payload
    try:
        data = json.loads(raw_payload)
        # Handle the webhook data...
        return HttpResponse("OK", status=200)
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return HttpResponse("Internal Server Error", status=500)
```

## Cashfree Dashboard Configuration

### 1. API Keys Setup
1. Log in to your Cashfree dashboard
2. Go to **Developers > API Keys**
3. Copy your **Client ID** and **Client Secret**
4. Use these in your environment variables

### 2. Webhook Configuration
1. Go to **Developers > Webhooks**
2. Add your webhook URL: `https://yourdomain.com/cashfree-webhook/`
3. Select the events you want to receive
4. **Important**: There is no webhook secret to configure - Cashfree uses your API Secret automatically

## Testing

Use the provided test script to verify your implementation:

```bash
python test_cashfree_webhook_verification.py
```

This script will:
- Generate a test signature using your API Secret
- Verify that your verification function works correctly
- Test rejection of invalid signatures

## Common Issues and Solutions

### Issue: 401 Unauthorized on webhook calls
**Solution**: Ensure `CASHFREE_CLIENT_SECRET` is properly configured in your environment variables.

### Issue: Signature verification always fails
**Solutions**:
1. Verify you're using the correct API Secret (Client Secret) from Cashfree dashboard
2. Ensure you're concatenating timestamp + payload in the correct order
3. Check that you're using the raw request body, not parsed JSON
4. Verify you're using HMAC SHA-256 and base64 encoding

### Issue: Looking for separate webhook secret
**Solution**: Cashfree does NOT provide a separate webhook secret. Use your API Secret (Client Secret) for webhook verification.

## Migration from Old Implementation

If you were previously using a separate `CASHFREE_SECRET_KEY`:

1. Remove `CASHFREE_SECRET_KEY` from your environment variables
2. Update your webhook verification to use `CASHFREE_CLIENT_SECRET`
3. Remove any references to webhook secrets in your documentation
4. Test the webhook verification with the new implementation

## Security Notes

- Always use `hmac.compare_digest()` for signature comparison to prevent timing attacks
- Validate the timestamp to prevent replay attacks (implement timestamp tolerance)
- Use HTTPS for all webhook endpoints
- Log verification failures for monitoring and debugging

## Files Modified

- `tapnex_ticketing_system/settings.py` - Removed separate webhook secret configuration
- `ticketing/views.py` - Updated verification function to use API Secret
- `fix_webhook_secret.py` - Updated diagnostic script
- `.env` - Removed webhook secret placeholder
- Created `test_cashfree_webhook_verification.py` - Verification test script

## Documentation References

- [Cashfree Webhook Documentation](https://docs.cashfree.com/docs/webhooks)
- [Cashfree API Authentication](https://docs.cashfree.com/docs/api-authentication)

---

**Summary**: Cashfree webhook verification is now correctly implemented using the API Secret (Client Secret) instead of looking for a non-existent separate webhook secret key.
