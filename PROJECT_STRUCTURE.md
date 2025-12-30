# Beaver Research Platform - Project Structure

This document provides a detailed overview of the backend and frontend structure for the Beaver Research application.

## 1. Backend Structure
**Location:** `/backend`
**Framework:** FastAPI (Python)

The backend is built as a modular RESTful API service using FastAPI. It handles data aggregation from various financial sources, user authentication, and serves data to the frontend.

### Key Technologies
- **FastAPI**: High-performance web framework.
- **SQLAlchemy (Async)**: ORM for database interactions.
- **Alembic**: Database migrations.
- **Pydantic**: Data validation and serialization.
- **Redis**: Caching and potential message brokering.
- **APScheduler**: Background tasks (though some scheduling code may be commented out).

### Directory Structure

```plaintext
/backend
├── alembic/                # Database migration scripts
├── config/                 # Configuration files
├── data/                   # Local data storage
├── migrations/             # Migration versions
├── routers/                # API Route Definitions
│   ├── auth.py             # User authentication and registration
│   ├── bond.py             # Bond market data
│   ├── energy.py           # Energy sector data
│   ├── external.py         # External API integrations
│   ├── internal.py         # Internal system data
│   ├── portfolio.py        # Portfolio management endpoints
│   ├── reports.py          # Report storage and retrieval
│   ├── research.py         # Research tools and data
│   ├── sec.py              # SEC EDGAR data integration
│   ├── stream_news.py      # News streaming endpoints
│   └── ...                 # Other domain-specific routers
├── schemas/                # Pydantic models for request/response validation
├── services/               # Business logic and external service integrations
│   ├── edgar_service.py    # Logic for fetching/parsing SEC filings
│   ├── research_engine.py  # Core research compilation logic
│   └── agent.py           # AI/Agentic service logic
├── uploads/                # Directory for user-uploaded files
├── database.py             # Database connection configuration
├── main.py                 # Application entry point
├── models.py               # SQL Database models
├── requirements.txt        # Python dependencies
└── rebuild_db.py           # Utility to reset the database
```

### Key Components
- **`main.py`**: Initializes the FastAPI app, configures CORS, logging, and database connections. It also creates default users on startup if they don't exist.
- **`routers/`**: The application is highly modular, with different domains of financial data (Bond, Energy, SEC, etc.) separated into their own routers.
- **`services/`**: logic for complex tasks like scraping SEC data (`edgar_service.py`) and processing research queries (`research_engine.py`).

---

## 2. Frontend Structure
**Location:** `/frontend`
**Framework:** Vue.js 3 + Vite

The frontend is a single-page application (SPA) focused on data visualization and financial analysis.

### Key Technologies
- **Vue.js 3**: Progressive JavaScript framework.
- **Vite**: Build tool and dev server.
- **Pinia**: State management.
- **Vue Router**: Client-side routing.
- **Chart.js / Vue-Chartjs**: Data visualization.
- **Tailwind CSS** (implied by class usage patterns, though vanilla CSS is also present).

### Directory Structure

```plaintext
/frontend
├── dist/                   # Production build output
├── public/                 # Static assets
├── src/
│   ├── assets/             # Images and styles
│   ├── components/         # Reusable UI components
│   │   ├── dashboard/      # Dashboard-specific widgets
│   │   ├── framework/      # Layout framework components
│   │   ├── investment/     # Investment-related tools
│   │   ├── ResearchChatSidebar.vue
│   │   └── ...
│   ├── composables/        # Shared logic (Vue Composables)
│   ├── config/             # Application configuration
│   ├── locales/            # i18n translation files
│   ├── router/             # Route definitions
│   ├── services/           # API client handling
│   ├── stores/             # Pinia state stores
│   ├── utils/              # Helper functions
│   ├── views/              # Page-level components
│   │   ├── Dashboard.vue
│   │   ├── PortfolioView.vue
│   │   ├── ResearchEditView.vue
│   │   ├── LoginView.vue
│   │   └── ...
│   ├── App.vue             # Root component
│   ├── main.js             # Entry point
│   └── style.css           # Global styles
├── index.html              # Entry HTML file
├── package.json            # Dependencies and scripts
└── vite.config.js          # Vite configuration
```

### Key Components
- **Views**: The application has distinct views for different financial sectors (Macro, Bond, Energy) and tools (Portfolio, Research Edit).
- **Stores**: Uses Pinia for managing global state, likely for user authentication and cached financial data.
- **Chart.js Integration**: Heavy reliance on charting libraries to display complex financial time-series data.

## 3. Integration Points
- **API Communication**: The frontend communicates with the backend via REST endpoints defined in the `routers/`, typically prefixed with `/api`.
- **Authentication**: JWT-based authentication flow handling login in `LoginView.vue` and token verification in the backend `auth.py`.
