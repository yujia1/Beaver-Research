# Financial Dashboard Data Sources

This dashboard aggregates data from various real-time and historical sources.

## Test User Credentials

For testing purposes, the following users have been created:

### Regular User
- **Username**: `testuser@gmail.com`
- **Password**: `testpass123`
- **Role**: `user`
- **Permissions**: Can view Market and Investment pages, but cannot add events

### Creator User
- **Username**: `creator@gmail.com`
- **Password**: `creator123`
- **Role**: `creator`
- **Permissions**: Can view Market and Investment pages, and can add/manage their own events on the timeline
### Admin User
- **Username**: `admin@gmail.com`
- **Password**: `admin123`
- **Role**: `admin`
### MinIO Console Access
- **Username**: `minioadmin`
- **Password**: `minioadmin`
- **URL**: `http://localhost:9001`

## 1. Macro Economics
-   **Source**: Yahoo Finance (`yfinance`)
-   **Indicators**:
    -   10Y Treasury Yield (`^TNX`)
    -   VIX (`^VIX`)
    -   S&P 500 (`^GSPC`)
-   **FRED API Key**: `d88880486954fc460aea0154b0ff827a` (now available for real data).

## 2. Micro Economics
-   **Source**: Yahoo Finance (`yfinance`)
-   **Data**: Real-time stock prices, volume, market cap, sector, and industry data for searched tickers.

## 3. Energy Dashboard
-   **Grid Status**: `gridstatus` Python Library
    -   **Source**: NYISO (New York Independent System Operator)
    -   **Data**: Real-time Fuel Mix, Real-time Load/Demand.
-   **Energy Prices**: Yahoo Finance (`yfinance`)
    -   **Crude Oil**: `CL=F`
    -   **Natural Gas**: `NG=F`
    -   **Data**: Historical prices (Days, Weekly, Monthly, Yearly, 5 Years).

## 4. AI Reports
-   **Source**: OpenAI API (`gpt-4o`)
-   **Data**: Generates reports based on uploaded documents (PDF/HTML) and context.

## Getting Started

### Prerequisites

- **Docker** and **Docker Compose** (recommended)
- **Python 3.11+** (for local development)
- **Node.js 22+** (for frontend development)

### Local Development with Docker Compose

The easiest way to run the application locally is using Docker Compose with PostgreSQL:

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your API keys
nano .env

# 3. Start all services (PostgreSQL, MinIO, Backend, Frontend)
docker-compose up -d

# 4. Check health
curl http://localhost:8000/health

# 5. Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# MinIO Console: http://localhost:9001
```

### Manual Setup (Alternative)

#### Backend Server

To start the backend server manually:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`
API documentation (Swagger UI) is available at `http://localhost:8000/docs`

#### Frontend Server

To start the frontend development server:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173` (or another port if 5173 is in use)

## Production Deployment

This application is production-ready with:
- ✅ PostgreSQL database with connection pooling
- ✅ Health check endpoints for monitoring
- ✅ Rate limiting for API protection
- ✅ Structured JSON logging
- ✅ Kubernetes manifests for cloud deployment
- ✅ CI/CD pipeline with GitHub Actions

### Deployment Options

1. **Kubernetes (Recommended for Production)**
   - See [k8s/README.md](k8s/README.md) for Kubernetes deployment
   - Supports AWS EKS, GKE, AKS
   - Includes autoscaling, health checks, and SSL/TLS

2. **Docker Compose (Development/Testing)**
   - Quick setup with `docker-compose up`
   - Suitable for local development and small deployments

For detailed deployment instructions, see:
- **[Deployment Guide](docs/deployment_guide.md)** - Comprehensive deployment documentation
- **[Kubernetes README](k8s/README.md)** - Kubernetes-specific instructions

### Health Monitoring

The application provides three health check endpoints:
- `/health` - Comprehensive health status (database, scheduler)
- `/health/ready` - Kubernetes readiness probe
- `/health/live` - Kubernetes liveness probe

## Architecture

- **Frontend**: Vue 3 + Vite + Chart.js
- **Backend**: FastAPI + Python 3.11
- **Database**: PostgreSQL (production) / SQLite (development fallback)
- **Object Storage**: MinIO (local) / S3 (production)
- **Deployment**: Docker + Kubernetes
- **CI/CD**: GitHub Actions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest` (backend) and `npm run build` (frontend)
5. Submit a pull request

## License

[Your License Here]

