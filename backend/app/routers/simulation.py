"""Simulation API router."""

import uuid
from fastapi import APIRouter, HTTPException

from app.models.schemas import SimulationStart, SimulationStatus
from app.services.job_manager import simulation_sessions

router = APIRouter()


@router.post("/start", response_model=SimulationStatus)
async def start_simulation(request: SimulationStart):
    """Start a new simulation session."""
    session_id = str(uuid.uuid4())[:8]
    
    # Store session info (actual execution happens via WebSocket)
    simulation_sessions[session_id] = {
        "status": "pending",
        "job_ids": request.job_ids,
        "test_names": request.test_names,
        "jobs_total": 0,
        "jobs_completed": 0,
    }
    
    return SimulationStatus(
        session_id=session_id,
        status="pending",
        jobs_total=0,
        jobs_completed=0
    )


@router.get("/status/{session_id}", response_model=SimulationStatus)
async def get_simulation_status(session_id: str):
    """Get status of a simulation session."""
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    
    session = simulation_sessions[session_id]
    return SimulationStatus(
        session_id=session_id,
        status=session.get("status", "unknown"),
        jobs_total=session.get("jobs_total", 0),
        jobs_completed=session.get("jobs_completed", 0),
        current_job=session.get("current_job")
    )


@router.post("/stop/{session_id}")
async def stop_simulation(session_id: str):
    """Stop a running simulation."""
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    
    simulation_sessions[session_id]["status"] = "stopped"
    return {"message": f"Simulation '{session_id}' stop requested"}
