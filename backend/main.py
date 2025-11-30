from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from routers import internal, external, agent, energy, sec, bond, reports, auth, events, research
from database import engine
import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Financial Dashboard Agent")

# CORS configuration
origins = [
    "http://localhost:5173",  # Vue.js dev server (default)
    "http://localhost:5174",  # Vue.js dev server (alternative port)
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(internal.router, prefix="/api/internal", tags=["Internal Data"])
app.include_router(external.router, prefix="/api/external", tags=["External Data"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
app.include_router(energy.router, prefix="/api/energy", tags=["Energy"])
app.include_router(sec.router, prefix="/api/sec", tags=["SEC Data"])
app.include_router(bond.router, prefix="/api/bond", tags=["Bond Data"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(research.router, prefix="/api/research", tags=["Research"])

@app.get("/")
def read_root():
    return {"message": "Financial Dashboard Agent API is running"}
