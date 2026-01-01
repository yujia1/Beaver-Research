# Stripe Embedded Checkout Setup Guide

## Overview
The payment system now uses Stripe's embedded checkout for a seamless payment experience.

## Backend Setup

### 1. Environment Variables
Add these to your `backend/.env` file:

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_PRICE_ID=price_your_price_id_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
FRONTEND_URL=http://localhost:5173
```

### 2. Get Stripe Keys
1. Go to https://dashboard.stripe.com/test/apikeys
2. Copy your **Secret key** (starts with `sk_test_`)
3. Copy your **Publishable key** (starts with `pk_test_`)

### 3. Create a Product & Price
1. Go to https://dashboard.stripe.com/test/products
2. Click "Add product"
3. Enter product details (e.g., "Premium Subscription - $19.99/month")
4. Set pricing (e.g., $19.99 recurring monthly)
5. Copy the **Price ID** (starts with `price_`)

### 4. Setup Webhook
1. Go to https://dashboard.stripe.com/test/webhooks
2. Click "Add endpoint"
3. Enter URL: `https://your-domain.com/api/payment/webhook`
4. Select events:
   - `checkout.session.completed`
   - `customer.subscription.deleted`
5. Copy the **Signing secret** (starts with `whsec_`)

## Frontend Setup

### 1. Environment Variables
Add to `frontend/.env`:

```env
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
```

### 2. Package Installation
Already installed: `@stripe/stripe-js`

## How It Works

### Payment Flow
1. User clicks "Upgrade" or visits `/pricing`
2. `PaymentGate.vue` component loads
3. Frontend calls `POST /api/payment/create-checkout-session`
4. Backend creates Stripe session and returns `clientSecret`
5. Stripe embedded checkout form renders in the page
6. User completes payment
7. Stripe redirects to `/payment/return?session_id=xxx`
8. Frontend calls `GET /api/payment/session-status`
9. Backend verifies payment and updates user
10. User is redirected to dashboard with premium access

### Webhook Flow
1. Stripe sends webhook to `/api/payment/webhook`
2. Backend verifies webhook signature
3. On `checkout.session.completed`: Set `user.has_paid = True`
4. On `customer.subscription.deleted`: Set `user.has_paid = False`

## Testing

### Test Cards
Use these test card numbers:
- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **3D Secure**: `4000 0025 0000 3155`

Any future expiry date and any 3-digit CVC.

### Local Testing with Stripe CLI
```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to local
stripe listen --forward-to localhost:8000/api/payment/webhook

# Copy the webhook signing secret to .env
```

## Files Modified

### Backend
- `routers/admin/payment.py` - Updated for embedded checkout
  - Changed `ui_mode` to `'embedded'`
  - Returns `clientSecret` instead of redirect URL
  - Added `/session-status` endpoint

### Frontend
- `components/PaymentGate.vue` - New embedded checkout UI
- `views/PaymentReturn.vue` - New return page
- `router/index.js` - Added `/payment/return` route
- `package.json` - Added `@stripe/stripe-js`

## Production Deployment

1. Replace all `sk_test_` and `pk_test_` keys with live keys
2. Update `FRONTEND_URL` to production domain
3. Update webhook endpoint URL in Stripe Dashboard
4. Test with real card (small amount)
5. Monitor webhook deliveries in Stripe Dashboard

## Troubleshooting

### Checkout doesn't load
- Check browser console for errors
- Verify `VITE_STRIPE_PUBLISHABLE_KEY` is set
- Ensure backend returns valid `clientSecret`

### Payment succeeds but user not upgraded
- Check webhook is configured correctly
- Verify webhook secret matches
- Check backend logs for webhook errors
- Test webhook delivery in Stripe Dashboard

### 403 errors after payment
- Clear browser cache and localStorage
- Re-login to refresh user data
- Check `has_paid` flag in database
