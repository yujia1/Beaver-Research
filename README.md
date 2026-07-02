# Beaver Research Platform

## Project Summary

- **Full-stack financial research platform** built with FastAPI (Python) backend and Vue.js 3 frontend, featuring real-time market data aggregation, AI-powered company analysis, and portfolio management with 50+ RESTful API endpoints serving data from 8+ external sources (Yahoo Finance, SEC EDGAR, FRED, OpenAI GPT-4)

- **Production-ready cloud infrastructure** with Docker Compose multi-service orchestration (PostgreSQL, Redis, MinIO), Kubernetes manifests for scalable deployment, comprehensive health monitoring, structured JSON logging, and Railway CI/CD pipeline supporting development, staging, and production environments

- **Enterprise security and authentication** implementing JWT-based auth, bcrypt password hashing, role-based access control (RBAC) with granular resource-level permissions across 4 user tiers (Admin, Creator, Contributor, User), and API rate limiting with SlowAPI

- **Advanced financial data integration** including automated SEC filing scraper (10-K, 10-Q, 8-K, 13F), real-time market data (stocks, bonds, commodities, currencies, crypto), macroeconomic indicators (GDP, unemployment, inflation, PMI), and AI-generated deep-dive research reports with financial statement analysis and peer comparisons

- **Scalable architecture with async operations** leveraging SQLAlchemy ORM with Alembic migrations, Redis caching for performance optimization, WebSocket streaming for live updates, Chart.js data visualization, internationalization (i18n) support, and modular codebase (~15,000 LOC) following separation of concerns with routers, services, schemas, and models

---

## Technology Stack

**Backend:** FastAPI, SQLAlchemy, PostgreSQL, Redis, Alembic, Pydantic, JWT, bcrypt, APScheduler  
**Frontend:** Vue.js 3, Pinia, Vue Router, Chart.js, Vite, vue-i18n  
**Infrastructure:** Docker, Kubernetes, Railway, MinIO/S3, Nginx  
**APIs:** OpenAI GPT-4, Yahoo Finance, FRED, SEC EDGAR, Financial Modeling Prep

---

## Quick Start

```bash
# Backend
source .venv/bin/activate && pip install -r backend/requirements.txt
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Docker (Production)
docker-compose up -d
```

---

**Author:** Yujia Jia | Full-Stack Developer
