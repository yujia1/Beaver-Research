# Railway Deployment Environment Variables

## Backend Service Environment Variables

Add these to your Railway backend service:

### Database
```
DATABASE_URL=postgresql://user:password@host:port/database
```
Get this from Railway PostgreSQL plugin

### Redis
```
REDIS_HOST=your-redis-host.railway.app
REDIS_PORT=6379
REDIS_DB=0
```
Get this from Railway Redis plugin

### S3 Storage (Railway Object Storage)
```
MINIO_ENDPOINT=storage.railway.app
MINIO_ACCESS_KEY=tid_mONkjQfnkD_a_MsgbYZZdIPQDQdaCEEaANM0uvcgADYdpEqoa0
MINIO_SECRET_KEY=tsec_bYwaSs-wuJ-tI18gR0fJ42f3dWzb7Xcr0f6-Hqe+zi4adVxUNvriXuzvhywRAfqiDh-SGU
MINIO_BUCKET=wrapped-rack-yu0io3hsokmf
MINIO_USE_SSL=true
```

### JWT & Security
```
SECRET_KEY=your-secret-key-here-generate-a-strong-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### API Keys (if using external services)
```
OPENAI_API_KEY=your-openai-key
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key
```

### CORS (Frontend URL)
```
FRONTEND_URL=https://your-frontend.railway.app
```

## Frontend Service Environment Variables

Add these to your Railway frontend service:

### Backend API URL
```
VITE_API_URL=https://your-backend.railway.app
```

## Important Notes

1. **Never commit these values to Git** - Use Railway's environment variable UI
2. **S3 Endpoint**: Railway's S3 is at `storage.railway.app` (already HTTPS)
3. **Database**: Use Railway's PostgreSQL plugin for production database
4. **Redis**: Use Railway's Redis plugin for caching
5. **CORS**: Make sure to set FRONTEND_URL to allow cross-origin requests

## Deployment Steps

### Backend:
1. Create new Railway service from GitHub repo
2. Set root directory to `/backend`
3. Add all environment variables above
4. Deploy

### Frontend:
1. Create new Railway service from same GitHub repo
2. Set root directory to `/frontend`
3. Add `VITE_API_URL` environment variable
4. Deploy

### Database & Redis:
1. Add PostgreSQL plugin to your Railway project
2. Add Redis plugin to your Railway project
3. Copy connection strings to backend environment variables
