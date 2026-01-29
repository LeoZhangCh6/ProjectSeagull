"""FastAPI backend for ProjectSeagull."""

import os
import sys

# Add project root to path for imports
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_HERE)
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import signals, tests, jobs, agents, simulation, visual_designer
from app.websocket.handler import router as websocket_router

app = FastAPI(
    title="ProjectSeagull API",
    description="Backend API for ProjectSeagull backtesting platform",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
app.include_router(tests.router, prefix="/api/tests", tags=["tests"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["simulation"])
app.include_router(visual_designer.router, prefix="/api/visual-designer", tags=["visual-designer"])
app.include_router(websocket_router)


@app.get("/")
async def root():
    return {"message": "ProjectSeagull API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
