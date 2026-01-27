"""Agents API router."""

from typing import List
from fastapi import APIRouter, HTTPException

from Common.db import get_pg_conn
from app.models.schemas import AgentCreate, AgentResponse, AgentClone

router = APIRouter()


@router.get("", response_model=List[AgentResponse])
async def list_agents():
    """List all agents."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT name, path, code, description, enabled
                    FROM agents_registry
                    ORDER BY name
                    """
                )
                rows = cur.fetchall()
        
        return [
            AgentResponse(
                name=row[0],
                path=row[1],
                code=row[2],
                description=row[3],
                enabled=row[4]
            )
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_name}", response_model=AgentResponse)
async def get_agent(agent_name: str):
    """Get a specific agent."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT name, path, code, description, enabled
                    FROM agents_registry
                    WHERE name = %s
                    """,
                    (agent_name,)
                )
                row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        return AgentResponse(
            name=row[0],
            path=row[1],
            code=row[2],
            description=row[3],
            enabled=row[4]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=AgentResponse)
async def create_agent(agent: AgentCreate):
    """Create or update an agent."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO agents_registry (name, path, code, description, enabled)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE
                    SET path = EXCLUDED.path,
                        code = EXCLUDED.code,
                        description = EXCLUDED.description,
                        enabled = EXCLUDED.enabled
                    """,
                    (agent.name, agent.path, agent.code, agent.description, agent.enabled)
                )
            conn.commit()
        
        return agent
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clone", response_model=AgentResponse)
async def clone_agent(clone_request: AgentClone):
    """Clone an existing agent with a new name."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                # Get source agent
                cur.execute(
                    """
                    SELECT path, code, description
                    FROM agents_registry
                    WHERE name = %s
                    """,
                    (clone_request.source_name,)
                )
                source = cur.fetchone()
                
                if not source:
                    raise HTTPException(
                        status_code=404, 
                        detail=f"Source agent '{clone_request.source_name}' not found"
                    )
                
                path, code, description = source
                new_path = f"db://agents/{clone_request.new_name}"
                new_description = f"Clone of {clone_request.source_name}"
                
                # Create new agent with copied code
                cur.execute(
                    """
                    INSERT INTO agents_registry (name, path, code, description, enabled)
                    VALUES (%s, %s, %s, %s, TRUE)
                    ON CONFLICT (name) DO UPDATE
                    SET path = EXCLUDED.path,
                        code = EXCLUDED.code,
                        description = EXCLUDED.description
                    """,
                    (clone_request.new_name, new_path, code, new_description)
                )
            conn.commit()
        
        return AgentResponse(
            name=clone_request.new_name,
            path=new_path,
            code=code,
            description=new_description,
            enabled=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_name}")
async def delete_agent(agent_name: str):
    """Delete an agent."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM agents_registry WHERE name = %s",
                    (agent_name,)
                )
            conn.commit()
        
        return {"message": f"Agent '{agent_name}' deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{agent_name}/toggle")
async def toggle_agent(agent_name: str):
    """Toggle agent enabled status."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE agents_registry
                    SET enabled = NOT enabled
                    WHERE name = %s
                    RETURNING enabled
                    """,
                    (agent_name,)
                )
                result = cur.fetchone()
            conn.commit()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        return {"name": agent_name, "enabled": result[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
