# Environment Setup Summary

## ✅ Files Created

### Frontend Environment Files
1. **`.env.staging`** - Active staging configuration
2. **`.env.production`** - Production template (update before going live)
3. **`ENV_CONFIG.md`** - Comprehensive documentation

### Updated Files
- **`package.json`** - Added `build:staging` and `build:production` scripts

## 📋 Railway Configuration

### Current Staging Service
**Service Name**: beaver-research-frontend-stage

**Build Method**: Dockerfile

**Dockerfile**: `frontend/Dockerfile`
- Uses `npm run build:staging`
- Loads `.env.staging`
- Builds with test Stripe keys

**No additional configuration needed** - just commit and push!

### Future Production Service
**Service Name**: beaver-research-frontend-prod (when created)

**Build Method**: Dockerfile

**Dockerfile Path**: `frontend/Dockerfile.production`
- Uses `npm run build:production`
- Loads `.env.production`
- Builds with live Stripe keys

**Setup Steps**:
1. Create new Railway service
2. Set **Dockerfile Path** to `Dockerfile.production`
3. Deploy

## 🚀 Next Steps

### 1. Commit and Push
```bash
git add frontend/.env.staging frontend/.env.production frontend/Dockerfile frontend/Dockerfile.production frontend/package.json frontend/ENV_CONFIG.md ENVIRONMENT_SETUP.md
git commit -m "Add staging and production environment configurations"
git push
```

### 2. Railway Auto-Deploys
- Railway detects the push
- Builds using updated `Dockerfile`
- Runs `npm run build:staging`
- Loads `.env.staging` with Stripe key
- Deploys automatically ✅

### 3. Verify Deployment
After Railway rebuilds (~2-3 minutes):
1. Visit https://stage.beaver-research.cloud/pricing
2. Open browser console (F12)
3. Look for:
   ```
   VITE_STRIPE_PUBLISHABLE_KEY: pk_test_51ReGdsGas9H...
   Stripe publishable key configured: true
   ```
4. Stripe checkout form should load ✅

## 📝 Environment Variable Locations

### Staging
- **Frontend**: `frontend/.env.staging` (committed to git)
- **Backend**: Railway environment variables
  - `STRIPE_SECRET_KEY`
  - `STRIPE_PRICE_MONTHLY`
  - `STRIPE_PRICE_ANNUAL`
  - `STRIPE_WEBHOOK_SECRET`
  - `FRONTEND_URL`

### Production (Future)
- **Frontend**: `frontend/.env.production` (update before deployment)
- **Backend**: Railway production environment variables (same keys, live values)

## 🔐 Security Checklist

✅ **Safe to commit**:
- `.env.staging` (contains only publishable keys)
- `.env.production` (contains only publishable keys)

❌ **Never commit**:
- `.env` (local development, in `.gitignore`)
- Backend secret keys (only in Railway env vars)

## 🎯 Current Status

- ✅ Staging environment files created
- ✅ Production template created
- ✅ Build scripts added
- ✅ Documentation complete
- ⏳ **Pending**: Update Railway build command
- ⏳ **Pending**: Commit and push changes
- ⏳ **Pending**: Verify deployment

## 📞 Support

If Stripe still doesn't load after deployment:
1. Check Railway build logs for errors
2. Verify build command is `npm run build:staging`
3. Check browser console for environment variable values
4. Ensure `.env.staging` is committed and pushed
