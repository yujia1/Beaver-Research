# Frontend Environment Configuration

This directory contains environment-specific configuration files for the Beaver Research frontend.

## Environment Files

### `.env.staging`
- **Purpose**: Staging/testing environment
- **URL**: https://stage.beaver-research.cloud
- **API**: https://api-stage.beaver-research.cloud
- **Stripe**: Test mode keys (`pk_test_...`)
- **Status**: ✅ Currently active

### `.env.production`
- **Purpose**: Production environment (future)
- **URL**: https://beaver-research.cloud
- **API**: https://api.beaver-research.cloud
- **Stripe**: Live mode keys (`pk_live_...`)
- **Status**: ⏳ Template only - update before production deployment

### `.env` (local development)
- **Purpose**: Local development
- **URL**: http://localhost:5173
- **API**: http://localhost:8000
- **Status**: Not committed to git (in `.gitignore`)

## How Vite Loads Environment Files

Vite loads environment files in this order:

1. `.env` - Loaded in all cases
2. `.env.local` - Loaded in all cases, ignored by git
3. `.env.[mode]` - Only loaded in specified mode (e.g., `.env.production`)
4. `.env.[mode].local` - Only loaded in specified mode, ignored by git

## Build Commands

### Staging Build
```bash
# Railway automatically uses .env.production by default
# To use staging, you need to specify the mode:
npm run build -- --mode staging
```

### Production Build
```bash
npm run build
# This uses .env.production by default
```

### Local Development
```bash
npm run dev
# This uses .env and .env.local
```

## Railway Configuration

### Current Setup (Staging)
**Service**: beaver-research-frontend-stage
**Build Command**: 
```bash
npm run build -- --mode staging
```
**Environment**: Uses `.env.staging`

### Future Setup (Production)
**Service**: beaver-research-frontend-prod
**Build Command**: 
```bash
npm run build
```
**Environment**: Uses `.env.production`

## Updating Environment Variables

### For Staging
1. Edit `frontend/.env.staging`
2. Commit and push changes
3. Railway will rebuild automatically

### For Production (when ready)
1. Get production Stripe keys from Stripe Dashboard
2. Update `frontend/.env.production` with:
   - Production API URL
   - Live Stripe publishable key (`pk_live_...`)
3. Commit and push
4. Deploy to production Railway service

## Security Notes

- ✅ **Publishable keys** (`pk_test_...`, `pk_live_...`) are safe to commit
- ✅ These files can be committed to git
- ❌ **Secret keys** (`sk_test_...`, `sk_live_...`) should NEVER be in frontend
- ❌ Backend secret keys belong in backend `.env` only

## Troubleshooting

### Environment variables not loading?
1. Check that you're using the correct build mode
2. Verify the file exists: `frontend/.env.[mode]`
3. Restart dev server or rebuild for production
4. Check browser console for loaded values

### Stripe not working?
1. Verify `VITE_STRIPE_PUBLISHABLE_KEY` is set
2. Check it starts with `pk_test_` (staging) or `pk_live_` (production)
3. Ensure the key matches the backend's secret key environment

## Example: Switching to Production

When ready to go live:

1. **Update `.env.production`:**
   ```env
   VITE_API_URL=https://api.beaver-research.cloud
   VITE_STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_LIVE_KEY_HERE
   ```

2. **Update backend production env:**
   ```env
   STRIPE_SECRET_KEY=sk_live_YOUR_LIVE_SECRET_HERE
   STRIPE_PRICE_MONTHLY=price_LIVE_MONTHLY_ID
   STRIPE_PRICE_ANNUAL=price_LIVE_ANNUAL_ID
   ```

3. **Deploy both services**

4. **Test with real card** (small amount first!)

5. **Update Stripe webhook** to production URL
