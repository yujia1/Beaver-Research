# Beaver Research Platform - Architecture Review

## Executive Summary

The Beaver Research Platform is a full-stack financial research application built with FastAPI (Python) backend and Vue.js 3 frontend. It aggregates real-time market data from multiple sources, provides AI-powered company analysis, and includes portfolio management capabilities.

---

## 1. Architecture & Design

### 1.1 System Architecture

**Architecture Pattern:** Microservices-oriented monolith with modular design

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Vue.js 3)                     │
│  - SPA with Vue Router                                      │
│  - Pinia for state management                               │
│  - Chart.js for data visualization                          │
│  - i18n support (English/Chinese)                           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST + WebSocket (SSE)
┌──────────────────────▼──────────────────────────────────────┐
│                  Backend (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Layer (Routers)                                 │  │
│  │  - /api/auth (Authentication)                         │  │
│  │  - /api/market/* (Market data)                        │  │
│  │  - /api/research (Research tools)                    │  │
│  │  - /api/portfolio (Portfolio management)             │  │
│  │  - /api/quant/* (Quantitative analysis)             │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                           │
│  ┌──────────────▼───────────────────────────────────────┐  │
│  │  Service Layer                                        │  │
│  │  - Market data aggregation                           │  │
│  │  - AI/Research engine                                │  │
│  │  - Scheduler (background tasks)                       │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                           │
│  ┌──────────────▼───────────────────────────────────────┐  │
│  │  Data Access Layer                                    │  │
│  │  - SQLAlchemy ORM                                     │  │
│  │  - Redis (caching/pubsub)                            │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌─────▼─────┐ ┌─────▼─────┐
│  PostgreSQL  │ │   Redis    │ │   MinIO   │
│  (Primary DB)│ │  (Cache)   │ │  (S3-like)│
└──────────────┘ └────────────┘ └───────────┘
```

### 1.2 Technology Stack

#### Backend
- **Framework:** FastAPI (async Python web framework)
- **ORM:** SQLAlchemy with async support
- **Database:** PostgreSQL (production) / SQLite (development)
- **Cache/Message Broker:** Redis
- **Migrations:** Alembic
- **Authentication:** JWT (JSON Web Tokens) with bcrypt password hashing
- **Scheduler:** APScheduler (AsyncIOScheduler)
- **Rate Limiting:** SlowAPI
- **Object Storage:** MinIO (S3-compatible) for report storage
- **AI Integration:** OpenAI GPT-4 API

#### Frontend
- **Framework:** Vue.js 3 (Composition API)
- **State Management:** Pinia
- **Routing:** Vue Router
- **Build Tool:** Vite
- **Charts:** Chart.js
- **i18n:** vue-i18n
- **HTTP Client:** Native Fetch API

#### Infrastructure
- **Containerization:** Docker & Docker Compose
- **Orchestration:** Kubernetes (k8s manifests provided)
- **Deployment:** Railway (CI/CD)
- **Reverse Proxy:** Nginx (frontend)

### 1.3 Design Patterns

1. **Layered Architecture:**
   - **Routers:** Handle HTTP requests/responses, validation
   - **Services:** Business logic, external API integration
   - **Models:** Database schema definitions
   - **Schemas:** Pydantic models for request/response validation

2. **Dependency Injection:**
   - FastAPI's dependency system for database sessions
   - Role-based access control via dependencies

3. **Singleton Pattern:**
   - Redis client (`RedisClient` class)
   - Database session management

4. **Repository Pattern (implicit):**
   - SQLAlchemy models abstract database operations

5. **Observer Pattern:**
   - Redis pub/sub for real-time market data streaming

### 1.4 API Structure

The API is organized by domain:

```
/api/auth/*              - Authentication & authorization
/api/admin/*             - Admin operations (DB, AI reports, payments)
/api/market/equity/*     - Stock market data
/api/market/bond/*       - Bond market data
/api/market/commodity/*  - Commodity prices
/api/market/currency/*   - Currency exchange rates
/api/market/crypto/*     - Cryptocurrency data
/api/market/economic/*   - Macroeconomic indicators
/api/market/policy/*     - Policy data
/api/market/sec/*        - SEC EDGAR filings
/api/market/news/*       - Market news
/api/research/*          - Research tools & AI analysis
/api/agent/*             - AI agent endpoints
/api/portfolio/*         - Portfolio management
/api/reports/*           - Report storage/retrieval
/api/framework/*         - Framework analysis
/api/quant/*             - Quantitative analysis
/api/quant/screener/*    - Stock screening
/api/academy/*           - Educational content
/api/stream/*            - WebSocket/SSE streaming
```

### 1.5 Security Architecture

1. **Authentication:**
   - JWT-based token authentication
   - Token expiration: 30 days (configurable)
   - Password hashing: bcrypt with salt

2. **Authorization:**
   - Role-Based Access Control (RBAC)
   - 4 user roles: `admin`, `creator`, `contributor`, `user`
   - Resource-level permissions stored in `role_permissions` table
   - Dynamic permission checking via dependencies

3. **Rate Limiting:**
   - SlowAPI integration
   - Configurable per endpoint
   - Default: 60 requests/minute for health checks

4. **CORS:**
   - Configurable via environment variables
   - Supports multiple origins
   - Credentials enabled

5. **Payment Integration:**
   - Stripe integration for subscription management
   - Payment status tracked in user model

### 1.6 Background Processing

**Scheduler (APScheduler):**
- **Regional Indices:** Every 5 minutes
- **Major Indices:** Every 60 seconds
- **Crypto Data:** Every 60 seconds
- **Currency Data:** Every 60 seconds
- **Commodity Data:** Every 60 seconds
- **Economic Data:** Every 5 minutes
- **AI Market Report:** Daily at 9:20 AM EST (Mon-Fri)

All scheduled tasks:
1. Fetch data from external APIs
2. Cache results in Redis with appropriate TTL
3. Publish updates via Redis pub/sub for real-time streaming

---

## 2. Database Structure

### 2.1 Database Technology

- **Production:** PostgreSQL 15 (via Docker Compose or Kubernetes)
- **Development:** SQLite (fallback)
- **Connection Pooling:** QueuePool (20 connections, 40 max overflow)
- **Migrations:** Alembic (2 migrations currently)

### 2.2 Database Schema

#### Core Tables

**1. `users`**
- Primary user authentication and profile data
- **Key Fields:**
  - `id` (PK)
  - `email`, `username` (unique, indexed)
  - `hashed_password`
  - `role` (admin, creator, contributor, user)
  - `is_active`, `is_verified`
  - `has_paid`, `payment_transaction_id`, `payment_date`
  - `stripe_customer_id`, `stripe_subscription_id`
  - `settings` (JSON) - User preferences
  - `last_login`, `created_at`, `updated_at`

**2. `reports`**
- User-generated research reports
- **Key Fields:**
  - `id` (PK)
  - `user_id` (FK → users)
  - `title`, `content` (Text/Markdown)
  - `file_path` (S3/MinIO key for PDFs)
  - `report_type` (daily, logic, short, market)
  - `ticker` (optional)
  - `is_uploaded`
  - `created_at`, `updated_at`

**3. `portfolio_positions`**
- User portfolio holdings
- **Key Fields:**
  - `id` (PK)
  - `user_id` (FK → users)
  - `ticker`, `sector`
  - `last_updated`, `created_at`
  - **Unique Constraint:** `(user_id, ticker)`

**4. `portfolio_lots`**
- Individual purchase lots for positions
- **Key Fields:**
  - `id` (PK)
  - `position_id` (FK → portfolio_positions)
  - `purchase_date` (ISO string)
  - `quantity`, `cost_per_share`
  - `side` (LONG/SHORT)
  - `link`, `note`
  - `created_at`

**5. `position_analysis`**
- Analysis questions/answers for positions
- **Key Fields:**
  - `id` (PK)
  - `position_id` (FK → portfolio_positions)
  - `question_id`, `answer`, `score`
  - `created_at`, `updated_at`
  - **Unique Constraint:** `(position_id, question_id)`

**6. `role_permissions`**
- RBAC permission matrix
- **Key Fields:**
  - `id` (PK)
  - `role` (indexed)
  - `resource` (indexed) - e.g., "/research", "/portfolio"
  - `can_access` (boolean)
  - `updated_at`
  - **Unique Constraint:** `(role, resource)`

#### Stock Screener Tables

**7. `stock_universe`**
- Cache of U.S. stock universe to avoid repeated API calls
- **Key Fields:**
  - `id` (PK)
  - `ticker` (unique, indexed)
  - `company_name`, `exchange`, `sector`, `industry`
  - `market_cap` (BigInteger)
  - `is_active`
  - `last_updated`, `created_at`

**8. `screening_runs`**
- Metadata for batch screening operations
- **Key Fields:**
  - `id` (PK)
  - `run_date` (indexed)
  - `total_stocks_processed`, `total_flagged`
  - `strategies_run` (JSON array)
  - `status` (running, completed, failed)
  - `error_log`, `duration_seconds`
  - `completed_at`

**9. `flagged_companies`**
- Companies flagged by screening criteria
- **Key Fields:**
  - `id` (PK)
  - `ticker` (indexed)
  - `company_name`, `sector`
  - `screening_run_id` (FK → screening_runs, nullable)
  - `screening_date` (indexed)
  - `strategies_flagged` (JSON array)
  - `metrics` (JSON) - Calculated metrics
  - `red_flags` (JSON) - Specific red flags
  - `financial_data` (JSON) - 5-year financial snapshot
  - **Unique Constraint:** `(ticker, screening_date)`

**10. `financial_statement_cache`**
- Permanent storage for financial statements (beyond Redis TTL)
- **Key Fields:**
  - `id` (PK)
  - `ticker` (indexed)
  - `statement_type` (income, cashflow, balance)
  - `fiscal_year`, `period` (annual/quarter)
  - `data` (JSON) - Full statement data
  - `fetched_at`, `source`
  - **Unique Constraint:** `(ticker, statement_type, fiscal_year, period)`

### 2.3 Database Relationships

```
users (1) ──< (N) reports
users (1) ──< (N) portfolio_positions
portfolio_positions (1) ──< (N) portfolio_lots
portfolio_positions (1) ──< (N) position_analysis
screening_runs (1) ──< (N) flagged_companies
```

### 2.4 Indexes

**Performance Indexes:**
- `users`: `email`, `username`, `stripe_customer_id`
- `reports`: `user_id`, `report_type`, `ticker`
- `portfolio_positions`: `user_id`, `ticker`
- `portfolio_lots`: `position_id`
- `position_analysis`: `position_id`
- `role_permissions`: `role`, `resource`
- `stock_universe`: `ticker` (unique)
- `flagged_companies`: `ticker`, `screening_date`, `screening_run_id`
- `financial_statement_cache`: `ticker`

### 2.5 Migration History

1. **Initial Schema (`d9360293cda9`):**
   - Created core tables: users, reports, portfolio_positions, portfolio_lots, position_analysis

2. **Stock Screener Models (`deebfac90985`):**
   - Added: stock_universe, screening_runs, flagged_companies, financial_statement_cache, role_permissions

### 2.6 Database Initialization

**Startup Sequence (from `main.py`):**
1. Check `REBUILD_DB` environment variable
2. If `true`: Drop all tables (with CASCADE for PostgreSQL), recreate from models
3. If `false`: Ensure tables exist (create if missing)
4. Validate schema (check for critical columns like `users.settings`)
5. Initialize default users (admin, creator, contributor, user)
6. Initialize default permissions (RBAC matrix)

---

## 3. Log Flow

### 3.1 Logging Architecture

**Logging Framework:** Python `logging` module with custom JSON formatter

**Configuration Location:** `backend/main.py` (lines 13-31)

### 3.2 Log Format

**Structured JSON Logging:**
```json
{
  "timestamp": "2025-01-15T10:30:45.123456",
  "level": "INFO",
  "message": "Environment variables loaded",
  "module": "main",
  "function": "<module>",
  "exception": "..." // Only if exception occurred
}
```

**Formatter Class:** `JSONFormatter` (custom class in `main.py`)
- Converts log records to JSON
- Includes timestamp (UTC ISO format)
- Includes module and function name
- Includes exception traceback if present

### 3.3 Log Levels

- **INFO:** General informational messages
- **WARNING:** Non-critical issues (e.g., Redis connection failures)
- **ERROR:** Error conditions that don't stop the application
- **DEBUG:** Not currently used (would require level change)

### 3.4 Log Output

**Handler:** `StreamHandler` (stdout/stderr)
- All logs go to standard output
- In containerized environments, captured by Docker/Kubernetes logging
- Suitable for log aggregation tools (e.g., ELK, CloudWatch, Datadog)

### 3.5 Logging Points

#### Application Startup
```python
logger.info("Environment variables loaded")
logger.info("FastAPI application initialized")
logger.info("Running startup initialization...")
logger.info("Database tables verified/created")
logger.info("Default permissions initialized/verified")
logger.error("Failed to rebuild database schema: {e}")  # On errors
```

#### Database Operations
```python
logger.info("Database engine created with PostgreSQL connection pooling")
logger.warning("Using SQLite database - NOT recommended for production")
logger.error("Database health check failed: {e}")
```

#### Redis Operations
```python
logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
logger.warning(f"Failed to connect to Redis at {REDIS_HOST}:{REDIS_PORT}. Caching disabled.")
logger.warning(f"Redis get error for key {key}: {str(e)}")
```

#### Scheduler Operations
```python
print(f"Scheduler: Updating regional indices...")  # Note: Uses print, not logger
print(f"Scheduler Error (Regional Indices): {e}")
```

**Note:** Scheduler uses `print()` instead of `logger` - this is inconsistent and should be standardized.

#### Stream Operations
```python
logger.info("Client disconnected from stream")
logger.error(f"Stream error: {e}")
```

### 3.6 Log Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│  Application Code                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Routers    │  │   Services   │  │  Scheduler   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                  │          │
│         └─────────────────┼──────────────────┘          │
│                           │                             │
│                    ┌──────▼──────┐                      │
│                    │   Logger    │                      │
│                    │  (module)   │                      │
│                    └──────┬──────┘                      │
└───────────────────────────┼─────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │ JSONFormatter  │
                    │  (custom)      │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │ StreamHandler │
                    │   (stdout)    │
                    └───────┬────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐  ┌─────────▼────────┐  ┌───────▼──────┐
│   Docker     │  │   Kubernetes     │  │   Railway    │
│   Logs       │  │   Logs           │  │   Logs       │
└──────────────┘  └──────────────────┘  └──────────────┘
```

### 3.7 Logging Best Practices & Recommendations

**Current State:**
- ✅ Structured JSON logging implemented
- ✅ Timestamps in UTC ISO format
- ✅ Module/function context included
- ✅ Exception tracebacks captured

**Areas for Improvement:**
1. **Inconsistent Logging:** Scheduler uses `print()` instead of `logger`
2. **Log Level Configuration:** Currently hardcoded to INFO, should use environment variable
3. **Request Logging:** No middleware for HTTP request/response logging
4. **Correlation IDs:** No request ID tracking for distributed tracing
5. **Log Rotation:** Not configured (handled by container/orchestrator)
6. **Sensitive Data:** Ensure passwords/tokens are not logged

**Recommended Enhancements:**
```python
# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    return response

# Use environment variable for log level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, LOG_LEVEL), handlers=[handler])
```

### 3.8 Log Aggregation (Production)

**Recommended Setup:**
- **Kubernetes:** Use Fluentd/Fluent Bit → Elasticsearch/Kibana
- **Docker Compose:** Use logging driver → centralized log service
- **Railway:** Native log aggregation (check Railway dashboard)

---

## 4. Key Design Decisions

### 4.1 Why FastAPI?
- Async/await support for I/O-bound operations (API calls, DB queries)
- Automatic OpenAPI documentation
- Type validation via Pydantic
- High performance (comparable to Node.js/Go)

### 4.2 Why Redis?
- Fast caching for frequently accessed data (market data)
- Pub/sub for real-time streaming (SSE)
- Fail-open design (app works without Redis, just slower)

### 4.3 Why PostgreSQL?
- ACID compliance for financial data
- JSON support for flexible schemas (settings, metrics)
- Production-ready with connection pooling
- SQLite only for local development

### 4.4 Why Vue.js 3?
- Modern reactive framework
- Composition API for better code organization
- Good ecosystem (Pinia, Vue Router, Chart.js)
- Smaller bundle size than React

### 4.5 Why MinIO?
- S3-compatible API (can switch to AWS S3 easily)
- Self-hosted option for cost control
- Good for storing PDF reports and large files

---

## 5. Data Flow Examples

### 5.1 Market Data Flow

```
External API (Yahoo Finance, FRED, etc.)
    ↓
Service Layer (services/market/*)
    ↓
Redis Cache (with TTL)
    ↓
Router (routers/market/*)
    ↓
FastAPI Response
    ↓
Frontend (Vue.js)
```

**Real-time Updates:**
```
Scheduler Task
    ↓
Fetch Data
    ↓
Update Redis Cache
    ↓
Publish to Redis Pub/Sub ('market_updates')
    ↓
Stream Endpoint (/api/stream/market)
    ↓
SSE to Frontend
```

### 5.2 Authentication Flow

```
Frontend: POST /api/auth/login
    ↓
Backend: Verify credentials (bcrypt)
    ↓
Backend: Generate JWT token
    ↓
Backend: Return token + user info
    ↓
Frontend: Store token in localStorage
    ↓
Frontend: Include token in Authorization header
    ↓
Backend: Verify token on protected routes
```

### 5.3 Research/AI Analysis Flow

```
Frontend: POST /api/research/interpret
    ↓
Backend: Check permissions (RBAC)
    ↓
Backend: Check cache (in-memory, 6-hour TTL)
    ↓
If cache miss:
    ↓
Backend: Fetch financial data (multiple sources)
    ↓
Backend: Call OpenAI GPT-4 API
    ↓
Backend: Cache result
    ↓
Backend: Return interpretation
```

---

## 6. Deployment Architecture

### 6.1 Docker Compose (Development/Staging)

**Services:**
- `postgres`: PostgreSQL 15 database
- `backend`: FastAPI application
- `frontend`: Vue.js SPA (Nginx)
- `minio`: Object storage
- `redis`: Cache and pub/sub

**Network:** `beaver_network` (bridge)

**Volumes:** Persistent storage for postgres, minio, redis

### 6.2 Kubernetes (Production)

**Components:**
- **Namespace:** `beaver-research`
- **Deployments:** Backend (2 replicas), Frontend
- **Services:** ClusterIP for internal communication
- **ConfigMap:** Environment configuration
- **Secrets:** API keys, database credentials
- **Ingress:** External traffic routing
- **Health Checks:** Liveness and readiness probes

**Resource Limits:**
- Backend: 512Mi-1Gi memory, 250m-1000m CPU
- Frontend: Nginx (lightweight)

---

## 7. External Integrations

### 7.1 Data Sources
- **Yahoo Finance:** Stock prices, market data
- **SEC EDGAR:** Company filings (10-K, 10-Q, 8-K, 13F)
- **FRED (Federal Reserve):** Economic indicators
- **Financial Modeling Prep:** Financial statements, ratios
- **OpenAI GPT-4:** AI-powered analysis
- **Stripe:** Payment processing

### 7.2 API Rate Limiting
- External APIs may have rate limits
- Redis caching reduces API calls
- Scheduler batches updates to avoid spikes

---

## 8. Security Considerations

### 8.1 Current Security Measures
- ✅ JWT authentication
- ✅ Bcrypt password hashing
- ✅ RBAC with resource-level permissions
- ✅ CORS configuration
- ✅ Rate limiting (SlowAPI)
- ✅ Environment variable secrets

### 8.2 Recommendations
- 🔒 Use HTTPS in production (handled by Railway/K8s ingress)
- 🔒 Rotate JWT secret keys regularly
- 🔒 Implement API key rotation for external services
- 🔒 Add request ID tracking for audit logs
- 🔒 Consider adding request/response logging middleware
- 🔒 Validate and sanitize all user inputs (Pydantic helps)

---

## 9. Performance Optimizations

### 9.1 Current Optimizations
- ✅ Redis caching (reduces external API calls)
- ✅ Database connection pooling (PostgreSQL)
- ✅ Async/await for I/O operations
- ✅ Background scheduler (non-blocking)
- ✅ Indexed database columns

### 9.2 Potential Improvements
- Consider CDN for frontend static assets
- Implement database query result caching
- Add pagination for large result sets
- Use database read replicas for read-heavy operations
- Implement request batching where possible

---

## 10. Monitoring & Observability

### 10.1 Current Monitoring
- Health check endpoints (`/health`, `/health/ready`, `/health/live`)
- Structured JSON logging
- Database connection health checks

### 10.2 Recommended Additions
- Metrics endpoint (Prometheus format)
- APM (Application Performance Monitoring)
- Error tracking (Sentry, Rollbar)
- Uptime monitoring
- Database query performance monitoring

---

## Conclusion

The Beaver Research Platform demonstrates a well-architected, production-ready financial research application with:

- **Modular design** with clear separation of concerns
- **Scalable architecture** supporting horizontal scaling
- **Comprehensive security** with RBAC and JWT authentication
- **Real-time capabilities** via Redis pub/sub and SSE
- **Robust data layer** with PostgreSQL and Redis caching
- **Structured logging** for observability

The codebase follows best practices for FastAPI and Vue.js development, with room for incremental improvements in logging consistency and monitoring.

