"""Agents API router."""

from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from Common.db import get_pg_conn
from app.models.schemas import AgentCreate, AgentResponse, AgentClone, AgentRename

router = APIRouter()


@router.get("", response_model=List[AgentResponse])
async def list_agents():
    """List all agents with their linked visual design ID (if any)."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 
                        a.name, a.path, a.code, a.description, a.enabled,
                        vd.id as visual_design_id
                    FROM agents_registry a
                    LEFT JOIN visual_agent_designs vd ON vd.agent_name = a.name
                    ORDER BY a.name
                    """
                )
                rows = cur.fetchall()
        
        return [
            AgentResponse(
                name=row[0],
                path=row[1],
                code=row[2],
                description=row[3],
                enabled=row[4],
                visual_design_id=row[5]
            )
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_name}", response_model=AgentResponse)
async def get_agent(agent_name: str):
    """Get a specific agent with its linked visual design ID (if any)."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 
                        a.name, a.path, a.code, a.description, a.enabled,
                        vd.id as visual_design_id
                    FROM agents_registry a
                    LEFT JOIN visual_agent_designs vd ON vd.agent_name = a.name
                    WHERE a.name = %s
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
            enabled=row[4],
            visual_design_id=row[5]
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


@router.patch("/{agent_name}/rename", response_model=AgentResponse)
async def rename_agent(agent_name: str, rename_request: AgentRename):
    """Rename an agent and its linked visual design (if any)."""
    try:
        new_name = rename_request.new_name
        
        if not new_name or new_name.strip() == "":
            raise HTTPException(status_code=400, detail="New name cannot be empty")
        
        new_name = new_name.strip()
        
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                # Check if agent exists
                cur.execute(
                    "SELECT name FROM agents_registry WHERE name = %s",
                    (agent_name,)
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
                
                # Check if new name already exists
                cur.execute(
                    "SELECT name FROM agents_registry WHERE name = %s",
                    (new_name,)
                )
                if cur.fetchone():
                    raise HTTPException(status_code=400, detail=f"Agent '{new_name}' already exists")
                
                # Also rename the linked visual design (if any)
                cur.execute(
                    """
                    UPDATE visual_agent_designs
                    SET name = %s, agent_name = %s
                    WHERE agent_name = %s
                    """,
                    (new_name, new_name, agent_name)
                )
                
                # Rename the agent
                cur.execute(
                    """
                    UPDATE agents_registry
                    SET name = %s, path = %s
                    WHERE name = %s
                    RETURNING name, path, code, description, enabled
                    """,
                    (new_name, f"db://agents/{new_name}", agent_name)
                )
                row = cur.fetchone()
                
                # Get the visual_design_id if any
                cur.execute(
                    "SELECT id FROM visual_agent_designs WHERE agent_name = %s",
                    (new_name,)
                )
                design_row = cur.fetchone()
                visual_design_id = design_row[0] if design_row else None
                
            conn.commit()
        
        return AgentResponse(
            name=row[0],
            path=row[1],
            code=row[2],
            description=row[3],
            enabled=row[4],
            visual_design_id=visual_design_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=AgentResponse)
async def upload_agent(
    file: UploadFile = File(...),
    agent_name: str = Form(None),
    description: str = Form(None)
):
    """Upload a Python file to register as a new agent."""
    try:
        # Validate file is a Python file
        if not file.filename.endswith('.py'):
            raise HTTPException(status_code=400, detail="Only .py files are allowed")
        
        # Read file content
        content = await file.read()
        code = content.decode('utf-8')
        
        # Use provided name or derive from filename
        name = agent_name if agent_name else file.filename.replace('.py', '')
        name = name.strip()
        
        if not name:
            raise HTTPException(status_code=400, detail="Agent name cannot be empty")
        
        # Set default description if not provided
        agent_description = description if description else f"Uploaded from {file.filename}"
        
        path = f"db://agents/{name}"
        
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO agents_registry (name, path, code, description, enabled)
                    VALUES (%s, %s, %s, %s, TRUE)
                    ON CONFLICT (name) DO UPDATE
                    SET path = EXCLUDED.path,
                        code = EXCLUDED.code,
                        description = EXCLUDED.description
                    """,
                    (name, path, code, agent_description)
                )
            conn.commit()
        
        return AgentResponse(
            name=name,
            path=path,
            code=code,
            description=agent_description,
            enabled=True
        )
    except HTTPException:
        raise
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be a valid UTF-8 encoded Python file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
