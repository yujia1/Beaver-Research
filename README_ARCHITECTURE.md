# Data Architecture, Data Layer, and Structure

This document provides a comprehensive overview of the data architecture, data layer, and project structure for the Financial Dashboard Agent application.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Data Architecture](#data-architecture)
3. [Data Layer](#data-layer)
4. [API Layer](#api-layer)
5. [Frontend Data Management](#frontend-data-management)
6. [Data Flow](#data-flow)

---

## Project Structure

### Overall Architecture

```
beaver_research/
├── backend/                 # FastAPI backend application
│   ├── models.py           # SQLAlchemy database models
│   ├── database.py         # Database connection and session management
│   ├── main.py             # FastAPI application entry point
│   ├── requirements.txt    # Python dependencies
│   ├── routers/            # API route handlers
│   │   ├── auth.py         # Authentication & authorization
│   │   ├── events.py       # Event management
│   │   ├── reports.py      # Report management
│   │   ├── internal.py     # Internal data (macro, micro, fed)
│   │   ├── external.py     # External data uploads
│   │   ├── agent.py        # AI agent services
│   │   ├── energy.py       # Energy data
│   │   ├── sec.py          # SEC filings data
│   │   └── bond.py         # Bond data
│   └── services/           # Business logic services
│       ├── agent.py        # AI agent service
│       └── edgar_service.py # SEC EDGAR service
│
├── frontend/               # Vue.js frontend application
│   ├── src/
│   │   ├── App.vue         # Main application component
│   │   ├── main.js         # Application entry point
│   │   ├── router/         # Vue Router configuration
│   │   ├── components/     # Vue components
│   │   │   ├── Dashboard.vue      # Market dashboard
│   │   │   ├── TimelineView.vue    # Investment timeline
│   │   │   ├── BondView.vue        # Bond view
│   │   │   ├── EnergyView.vue      # Energy view
│   │   │   └── ...
│   │   └── utils/          # Utility functions
│   │       └── dailyCache.js # Client-side caching
│   └── package.json        # Node.js dependencies
│
└── docker-compose.yml      # Docker orchestration
```

---

## Data Architecture

### Architecture Pattern

The application follows a **3-tier architecture**:

1. **Presentation Layer** (Frontend - Vue.js)
   - User interface components
   - Client-side state management
   - Local storage for user preferences and temporary data

2. **Application Layer** (Backend - FastAPI)
   - API endpoints
   - Business logic
   - Authentication & authorization
   - Data validation

3. **Data Layer** (Database - SQLite/PostgreSQL)
   - Persistent data storage
   - Data relationships
   - Data integrity

### Data Flow Architecture

```
┌─────────────┐
│   Browser   │
│  (Vue.js)   │
└──────┬──────┘
       │ HTTP/REST API
       │ (JWT Authentication)
       ▼
┌─────────────┐
│   FastAPI   │
│  Backend    │
└──────┬──────┘
       │
       ├──► SQLAlchemy ORM
       │    └──► Database (SQLite/PostgreSQL)
       │
       ├──► External APIs
       │    ├──► FRED API (Economic data)
       │    ├──► Yahoo Finance (Stock data)
       │    ├──► OpenAI API (AI reports)
       │    ├──► SEC EDGAR (Filings)
       │    └──► GridStatus (Energy data)
       │
       └──► Local Storage (Frontend)
            ├──► User tokens
            ├──► User info
            ├──► Report data (per ticker)
            └──► Cache data
```

---

## Data Layer

### Database Models

The application uses **SQLAlchemy ORM** with the following models:

#### 1. User Model

```python
class User(Base):
    __tablename__ = "users"
    
    id: Integer (Primary Key)
    email: String (Unique, Indexed)
    username: String (Unique, Indexed)
    hashed_password: String
    role: String (Default: "user")
        # Values: "admin", "creator", "contributor", "user"
    is_active: Boolean (Default: True)
    created_at: DateTime (Timezone-aware)
    
    # Relationships
    events: Relationship (One-to-Many with Event)
```

**Purpose**: Stores user accounts with role-based access control.

**Indexes**: 
- `email` (unique)
- `username` (unique)

#### 2. Event Model

```python
class Event(Base):
    __tablename__ = "events"
    
    id: Integer (Primary Key)
    user_id: Integer (Foreign Key → users.id, Indexed)
    ticker: String (Indexed)
    date: DateTime (Timezone-aware)
    title: String
    description: Text
    type: String
        # Values: "positive", "negative", "neutral"
    category: String
        # Values: "macro", "micro", "market", "industry", "product"
    is_forecast: Boolean (Default: False)
    created_at: DateTime (Timezone-aware)
    updated_at: DateTime (Timezone-aware, Auto-update)
    
    # Relationships
    user: Relationship (Many-to-One with User)
```

**Purpose**: Stores timeline events associated with stock tickers, created by users with "creator" or "admin" roles.

**Indexes**:
- `user_id` (foreign key)
- `ticker` (for filtering by stock symbol)

**Constraints**:
- `user_id` must reference an existing user
- `type` must be one of: positive, negative, neutral
- `category` must be one of: macro, micro, market, industry, product

#### 3. Report Model

```python
class Report(Base):
    __tablename__ = "reports"
    
    id: Integer (Primary Key)
    title: String (Indexed)
    content: Text
    report_type: String
        # Values: "company_overview", "operating_drivers", 
        #         "notes_disclosures", "capital_structure", "deep_dive"
    ticker: String (Indexed)
    created_at: DateTime (Timezone-aware)
```

**Purpose**: Stores AI-generated reports and user-created reports associated with stock tickers.

**Indexes**:
- `title`
- `ticker` (for filtering by stock symbol)

### Database Configuration

**Location**: `backend/database.py`

```python
# Database URL (configurable via environment variable)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./financial_agent.db")

# Supports:
# - SQLite (default, for development)
# - PostgreSQL (production, via DATABASE_URL env var)
```

**Session Management**:
- Uses SQLAlchemy `SessionLocal` for database sessions
- Sessions are dependency-injected via FastAPI's `Depends(get_db)`
- Automatic session cleanup after request completion

### Data Relationships

```
User (1) ──< (Many) Event
  │
  └── One user can create many events

Event ──> (Many-to-One) User
  │
  └── Each event belongs to one user

Report (Independent)
  │
  └── Reports are associated with tickers, not users directly
```

---

## API Layer

### API Structure

The backend exposes RESTful APIs organized by domain:

#### Authentication API (`/api/auth`)

- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User authentication (returns JWT token)
- `GET /api/auth/me` - Get current user info
- `GET /api/auth/creators` - Get all creator/admin users
- `POST /api/auth/users` - Create user (admin only)

**Authentication**: JWT tokens (Bearer authentication)
**Token Expiry**: 30 days

#### Events API (`/api/events`)

- `GET /api/events/` - List events (filtered by ticker, creator_id)
- `POST /api/events/` - Create event (creator/admin only)
- `GET /api/events/{event_id}` - Get single event
- `PUT /api/events/{event_id}` - Update event (owner only)
- `DELETE /api/events/{event_id}` - Delete event (owner only)

**Query Parameters**:
- `ticker` (required): Stock symbol
- `creator_id` (optional): Filter by creator user ID

#### Reports API (`/api/reports`)

- `GET /api/reports/` - List all reports
- `POST /api/reports/` - Create report
- `GET /api/reports/{report_id}` - Get single report

#### Internal Data API (`/api/internal`)

- `GET /api/internal/macro/{ticker}` - Get macro economic data
- `GET /api/internal/macro/series/{series_id}` - Get specific economic series
- `GET /api/internal/micro/{ticker}` - Get micro economic (company) data

#### External Data API (`/api/external`)

- `POST /api/external/upload` - Upload document (PDF/HTML)

#### Agent API (`/api/agent`)

- `POST /api/agent/generate_report` - Generate AI report from context

#### Energy API (`/api/energy`)

- `GET /api/energy/grid` - Get grid status data
- `GET /api/energy/prices` - Get energy prices

#### SEC API (`/api/sec`)

- `GET /api/sec/filings/{ticker}` - Get SEC filings

#### Bond API (`/api/bond`)

- `GET /api/bond/data` - Get bond data

### API Data Formats

#### Request Format

**Authentication Header** (for protected endpoints):
```
Authorization: Bearer <JWT_TOKEN>
```

**Content-Type**: `application/json`

#### Response Format

**Success Response**:
```json
{
  "id": 1,
  "field1": "value1",
  "field2": "value2"
}
```

**Error Response**:
```json
{
  "detail": "Error message"
}
```

---

## Frontend Data Management

### State Management

The frontend uses **Vue 3 Composition API** with reactive refs and computed properties:

#### Global State (App.vue)

- `user`: Current logged-in user info
- `isAuthenticated`: Computed property for auth status
- Stored in `localStorage`:
  - `access_token`: JWT token
  - `user`: User object (JSON stringified)

#### Component State (TimelineView.vue)

**Stock Data**:
- `selectedStock`: Currently selected ticker
- `stockData`: Historical price data
- `currentPrice`, `priceChange`, `priceChangePercent`

**Events**:
- `events`: Array of event objects
- `filteredEvents`: Computed filtered events
- `selectedCreatorId`: Currently selected creator

**Report Data**:
- `reportContent`: Report text content
- `linkedCards`: Array of linked card objects
- Stored in `localStorage` with key: `report_{TICKER}`

**Company Data**:
- `companyData`: Company information
- `financialData`: Financial statements
- `ratiosData`: Financial ratios

#### Component State (Dashboard.vue)

**Market Data**:
- `equityIndicators`: Equity market indicators
- `bondIndicators`: Bond market indicators
- `economicIndicators`: Economic indicators
- `fedIndicators`: Federal Reserve indicators
- `energyIndicators`: Energy market indicators

### Client-Side Storage

#### localStorage Keys

| Key | Purpose | Format |
|-----|---------|--------|
| `access_token` | JWT authentication token | String |
| `user` | Current user object | JSON string |
| `flashcards_{TICKER}` | Flashcard deck per ticker | JSON array |
| `report_{TICKER}` | Report content and linked cards | JSON object |

#### Caching Strategy

**Location**: `frontend/src/utils/dailyCache.js`

- **Daily Cache**: Data cached with date-based expiration
- **Cache Keys**: Based on API endpoint and parameters
- **Automatic Expiration**: Cache invalidates at midnight

**Example**:
```javascript
// Cache key format: "api_endpoint_params_date"
const cacheKey = `macro_${ticker}_${new Date().toISOString().split('T')[0]}`
```

### Data Fetching Patterns

#### Authenticated Requests

```javascript
const token = localStorage.getItem('access_token')
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${token}`
}

const response = await fetch(url, { headers })
```

#### Unauthenticated Requests

```javascript
const response = await fetch(url, {
  headers: {
    'Content-Type': 'application/json'
  }
})
```

---

## Data Flow

### User Authentication Flow

```
1. User submits login form
   ↓
2. Frontend sends POST /api/auth/login
   ↓
3. Backend validates credentials
   ↓
4. Backend generates JWT token
   ↓
5. Frontend stores token in localStorage
   ↓
6. Frontend stores user info in localStorage
   ↓
7. Frontend includes token in subsequent requests
```

### Event Creation Flow

```
1. Creator user selects text/creates event
   ↓
2. Frontend sends POST /api/events/ with JWT token
   ↓
3. Backend validates token and user role
   ↓
4. Backend creates Event record in database
   ↓
5. Backend returns created event
   ↓
6. Frontend updates local events array
   ↓
7. Frontend refreshes timeline chart
```

### Report Data Flow

```
1. User writes report content
   ↓
2. User selects text and creates linked card
   ↓
3. Frontend stores in localStorage: report_{TICKER}
   ↓
4. Data structure:
   {
     content: "report HTML content",
     cards: [
       {
         id: "sentence_1",
         sentenceId: "sentence_1",
         content: "card content",
         sentenceText: "linked text"
       }
     ]
   }
   ↓
5. On ticker change, load report_{NEW_TICKER}
   ↓
6. Restore linked sentences in DOM
```

### Market Data Flow

```
1. User navigates to Market Dashboard
   ↓
2. Frontend requests data from /api/internal/macro
   ↓
3. Backend fetches from external APIs:
   - FRED API (economic data)
   - Yahoo Finance (stock data)
   ↓
4. Backend processes and returns data
   ↓
5. Frontend caches data (daily cache)
   ↓
6. Frontend renders charts and tables
```

### Real-time Data Updates

**Energy Data**:
- Fetched from GridStatus library
- Real-time grid status and fuel mix
- Updated on page load and manual refresh

**Stock Prices**:
- Fetched from Yahoo Finance
- Historical data with multiple timeframes
- Cached client-side for performance

---

## Data Validation

### Backend Validation

**Pydantic Models**: Used for request/response validation

**Example** (Event Creation):
```python
class EventCreate(BaseModel):
    ticker: str
    date: str  # ISO format
    title: str
    description: Optional[str] = ""
    type: str  # Must be: positive, negative, neutral
    category: str  # Must be: macro, micro, market, industry, product
    is_forecast: bool = False
```

**Password Validation**:
- Minimum length: 6 characters
- Maximum length: 12 characters
- Hashed using bcrypt (72-byte limit handled)

### Frontend Validation

- Form validation before API calls
- Type checking for API responses
- Error handling and user feedback

---

## Security Considerations

### Authentication

- **JWT Tokens**: Stateless authentication
- **Token Expiry**: 30 days
- **Password Hashing**: bcrypt with 12 rounds
- **Password Length**: 6-12 characters (enforced)

### Authorization

**Role-Based Access Control (RBAC)**:

| Role | Permissions |
|------|-------------|
| `admin` | Full access, can create users, manage all events |
| `creator` | Can create/manage own events, view all data |
| `contributor` | Can view and contribute (future feature) |
| `user` | Can view Market and Investment pages only |

### Data Protection

- **SQL Injection**: Prevented by SQLAlchemy ORM
- **XSS**: Input sanitization in contenteditable areas
- **CORS**: Configured for specific origins only
- **Sensitive Data**: Passwords never stored in plain text

---

## External Data Sources

### Economic Data (FRED API)

- **API Key**: Stored in environment variable
- **Endpoints**: Various economic indicators
- **Rate Limits**: Handled by backend

### Stock Data (Yahoo Finance)

- **Library**: `yfinance`
- **Data**: Real-time and historical prices
- **Caching**: Client-side daily cache

### AI Services (OpenAI)

- **Model**: GPT-4o
- **Usage**: Report generation from documents
- **API Key**: Stored in environment variable

### SEC Data (EDGAR)

- **Service**: `edgar_service.py`
- **Data**: Company filings and disclosures
- **Format**: HTML/PDF parsing

### Energy Data (GridStatus)

- **Library**: `gridstatus`
- **Source**: NYISO (New York Independent System Operator)
- **Data**: Real-time grid status and fuel mix

---

## Performance Optimizations

### Backend

- **Database Indexing**: On frequently queried fields (user_id, ticker)
- **Connection Pooling**: SQLAlchemy session management
- **Caching**: Consider Redis for production (not implemented)

### Frontend

- **Daily Cache**: Prevents redundant API calls
- **Lazy Loading**: Components loaded on demand
- **Debouncing**: For search inputs
- **Local Storage**: Reduces server load for user-specific data

---

## Future Enhancements

### Database

- [ ] Migrate to PostgreSQL for production
- [ ] Add database migrations (Alembic)
- [ ] Implement database backups
- [ ] Add full-text search for reports

### Caching

- [ ] Implement Redis for server-side caching
- [ ] Cache external API responses
- [ ] Implement cache invalidation strategies

### Data Analytics

- [ ] Add event analytics
- [ ] User activity tracking
- [ ] Report usage statistics

---

## Environment Variables

### Backend (.env)

```bash
DATABASE_URL=sqlite:///./financial_agent.db  # or PostgreSQL URL
SECRET_KEY=your-secret-key-change-this-in-production
FRED_API_KEY=your-fred-api-key
OPENAI_API_KEY=your-openai-api-key
```

### Frontend

No environment variables required (uses hardcoded API URLs for development)

---

## Database Schema Diagram

```
┌─────────────┐
│    users    │
├─────────────┤
│ id (PK)     │
│ email       │
│ username    │
│ password    │
│ role        │
│ is_active   │
│ created_at  │
└──────┬──────┘
       │
       │ 1:N
       │
       ▼
┌─────────────┐
│   events    │
├─────────────┤
│ id (PK)     │
│ user_id (FK)│──┐
│ ticker      │  │
│ date        │  │
│ title       │  │
│ description │  │
│ type        │  │
│ category    │  │
│ is_forecast │  │
│ created_at  │  │
│ updated_at  │  │
└─────────────┘  │
                 │
                 │ References
                 │
┌─────────────┐  │
│   reports   │  │
├─────────────┤  │
│ id (PK)     │  │
│ title       │  │
│ content     │  │
│ report_type │  │
│ ticker      │──┘ (No FK, but associated)
│ created_at  │
└─────────────┘
```

---

## Conclusion

This architecture provides:

- **Scalability**: Modular design allows easy extension
- **Security**: Role-based access control and secure authentication
- **Performance**: Client-side caching and efficient database queries
- **Maintainability**: Clear separation of concerns
- **Flexibility**: Support for multiple data sources and storage backends

For questions or contributions, please refer to the main README.md file.

