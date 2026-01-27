"""Jobs API router."""

from typing import List
from fastapi import APIRouter, HTTPException

from Common.db import get_pg_conn
from app.models.schemas import JobCreate, JobResponse

router = APIRouter()


@router.get("", response_model=List[JobResponse])
async def list_jobs():
    """List all jobs."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT test_name, agent_name
                    FROM test_jobs
                    ORDER BY test_name, agent_name
                    """
                )
                rows = cur.fetchall()
        
        return [
            JobResponse(test_name=row[0], agent_name=row[1])
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-tests")
async def list_available_tests():
    """List test names available for job creation."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM test_definitions ORDER BY name")
                rows = cur.fetchall()
        
        return [row[0] for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-agents")
async def list_available_agents():
    """List agent names available for job creation."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT name FROM agents_registry WHERE enabled = TRUE ORDER BY name"
                )
                rows = cur.fetchall()
        
        return [row[0] for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=JobResponse)
async def create_job(job: JobCreate):
    """Create a job (assign agent to test)."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO test_jobs (test_name, agent_name)
                    VALUES (%s, %s)
                    ON CONFLICT (test_name, agent_name) DO NOTHING
                    """,
                    (job.test_name, job.agent_name)
                )
            conn.commit()
        
        return job
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{test_name}/{agent_name}")
async def delete_job(test_name: str, agent_name: str):
    """Delete a job."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM test_jobs WHERE test_name = %s AND agent_name = %s",
                    (test_name, agent_name)
                )
            conn.commit()
        
        return {"message": f"Job '{test_name}/{agent_name}' deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("")
async def delete_all_jobs():
    """Delete all jobs."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM test_jobs")
            conn.commit()
        
        return {"message": "All jobs deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
