from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from routers import internal, external, agent, energy, sec, bond

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
)

app.include_router(internal.router, prefix="/api/internal", tags=["Internal Data"])
app.include_router(external.router, prefix="/api/external", tags=["External Data"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
app.include_router(energy.router, prefix="/api/energy", tags=["Energy"])
app.include_router(sec.router, prefix="/api/sec", tags=["SEC Data"])
app.include_router(bond.router, prefix="/api/bond", tags=["Bond Data"])

@app.get("/")
def read_root():
    return {"message": "Financial Dashboard Agent API is running"}
