"""Visual Agent Designer API router."""

import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException

from Common.db import get_pg_conn
from app.models.schemas import (
    VisualDesignCreate,
    VisualDesignUpdate,
    VisualDesignResponse,
    VisualDesignDeployRequest,
    CodeGenerationRequest,
    CodeGenerationResponse,
    ValidationResult,
    SignalPreviewRequest,
    SignalPreviewResponse,
)

router = APIRouter()


# ============================================================================
# CRUD Operations for Visual Designs
# ============================================================================

@router.get("", response_model=List[VisualDesignResponse])
async def list_designs():
    """List all visual agent designs."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, description, graph_json, symbol, 
                           primary_timespan, primary_multiplier, generated_code,
                           agent_name, created_at, updated_at
                    FROM visual_agent_designs
                    ORDER BY updated_at DESC
                    """
                )
                rows = cur.fetchall()
        
        return [
            VisualDesignResponse(
                id=row[0],
                name=row[1],
                description=row[2],
                graph_json=row[3] if isinstance(row[3], dict) else json.loads(row[3]) if row[3] else {},
                symbol=row[4],
                primary_timespan=row[5],
                primary_multiplier=row[6],
                generated_code=row[7],
                agent_name=row[8],
                created_at=str(row[9]) if row[9] else None,
                updated_at=str(row[10]) if row[10] else None,
            )
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{design_id}", response_model=VisualDesignResponse)
async def get_design(design_id: int):
    """Get a specific visual design."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, description, graph_json, symbol, 
                           primary_timespan, primary_multiplier, generated_code,
                           agent_name, created_at, updated_at
                    FROM visual_agent_designs
                    WHERE id = %s
                    """,
                    (design_id,)
                )
                row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Design {design_id} not found")
        
        return VisualDesignResponse(
            id=row[0],
            name=row[1],
            description=row[2],
            graph_json=row[3] if isinstance(row[3], dict) else json.loads(row[3]) if row[3] else {},
            symbol=row[4],
            primary_timespan=row[5],
            primary_multiplier=row[6],
            generated_code=row[7],
            agent_name=row[8],
            created_at=str(row[9]) if row[9] else None,
            updated_at=str(row[10]) if row[10] else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=VisualDesignResponse)
async def create_design(design: VisualDesignCreate):
    """Create a new visual design."""
    try:
        graph_json = design.graph_json.model_dump() if design.graph_json else {}
        
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO visual_agent_designs 
                    (name, description, graph_json, symbol, primary_timespan, primary_multiplier)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, created_at, updated_at
                    """,
                    (design.name, design.description, json.dumps(graph_json),
                     design.symbol, design.primary_timespan, design.primary_multiplier)
                )
                row = cur.fetchone()
            conn.commit()
        
        return VisualDesignResponse(
            id=row[0],
            name=design.name,
            description=design.description,
            graph_json=graph_json,
            symbol=design.symbol,
            primary_timespan=design.primary_timespan,
            primary_multiplier=design.primary_multiplier,
            created_at=str(row[1]),
            updated_at=str(row[2]),
        )
    except Exception as e:
        if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
            raise HTTPException(status_code=400, detail=f"Design '{design.name}' already exists")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{design_id}", response_model=VisualDesignResponse)
async def update_design(design_id: int, update: VisualDesignUpdate):
    """Update a visual design."""
    try:
        # Build dynamic update query
        update_fields = []
        values = []
        
        if update.name is not None:
            update_fields.append("name = %s")
            values.append(update.name)
        
        if update.description is not None:
            update_fields.append("description = %s")
            values.append(update.description)
        
        if update.graph_json is not None:
            update_fields.append("graph_json = %s")
            values.append(json.dumps(update.graph_json.model_dump()))
        
        if update.symbol is not None:
            update_fields.append("symbol = %s")
            values.append(update.symbol)
        
        if update.primary_timespan is not None:
            update_fields.append("primary_timespan = %s")
            values.append(update.primary_timespan)
        
        if update.primary_multiplier is not None:
            update_fields.append("primary_multiplier = %s")
            values.append(update.primary_multiplier)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        values.append(design_id)
        
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE visual_agent_designs
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                    RETURNING id, name, description, graph_json, symbol, 
                              primary_timespan, primary_multiplier, generated_code,
                              agent_name, created_at, updated_at
                    """,
                    values
                )
                row = cur.fetchone()
            conn.commit()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Design {design_id} not found")
        
        return VisualDesignResponse(
            id=row[0],
            name=row[1],
            description=row[2],
            graph_json=row[3] if isinstance(row[3], dict) else json.loads(row[3]) if row[3] else {},
            symbol=row[4],
            primary_timespan=row[5],
            primary_multiplier=row[6],
            generated_code=row[7],
            agent_name=row[8],
            created_at=str(row[9]) if row[9] else None,
            updated_at=str(row[10]) if row[10] else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{design_id}")
async def delete_design(design_id: int):
    """Delete a visual design."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM visual_agent_designs WHERE id = %s RETURNING name",
                    (design_id,)
                )
                row = cur.fetchone()
            conn.commit()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Design {design_id} not found")
        
        return {"message": f"Design '{row[0]}' deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Code Generation
# ============================================================================

@router.post("/generate-code", response_model=CodeGenerationResponse)
async def generate_code(request: CodeGenerationRequest):
    """Generate Python code from a visual design graph."""
    from app.services.code_generator import generate_agent_code
    
    try:
        result = generate_agent_code(
            graph=request.graph_json.model_dump(),
            symbol=request.symbol,
            primary_timespan=request.primary_timespan,
            primary_multiplier=request.primary_multiplier,
        )
        return result
    except Exception as e:
        return CodeGenerationResponse(
            code="",
            errors=[str(e)],
        )


@router.post("/{design_id}/generate", response_model=CodeGenerationResponse)
async def generate_code_for_design(design_id: int):
    """Generate and save code for a specific design."""
    from app.services.code_generator import generate_agent_code
    
    try:
        # Get the design
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT graph_json, symbol, primary_timespan, primary_multiplier
                    FROM visual_agent_designs
                    WHERE id = %s
                    """,
                    (design_id,)
                )
                row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Design {design_id} not found")
        
        graph_json = row[0] if isinstance(row[0], dict) else json.loads(row[0]) if row[0] else {}
        
        # Generate code
        result = generate_agent_code(
            graph=graph_json,
            symbol=row[1],
            primary_timespan=row[2],
            primary_multiplier=row[3],
        )
        
        # Save generated code
        if result.code and not result.errors:
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE visual_agent_designs SET generated_code = %s WHERE id = %s",
                        (result.code, design_id)
                    )
                conn.commit()
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        return CodeGenerationResponse(
            code="",
            errors=[str(e)],
        )


# ============================================================================
# Validation
# ============================================================================

@router.post("/validate", response_model=ValidationResult)
async def validate_graph(request: CodeGenerationRequest):
    """Validate a visual design graph for errors."""
    from app.services.graph_validator import validate_graph
    
    try:
        return validate_graph(request.graph_json.model_dump())
    except Exception as e:
        return ValidationResult(
            valid=False,
            errors=[{"node_id": None, "message": str(e)}],
        )


# ============================================================================
# Deploy as Agent
# ============================================================================

@router.post("/{design_id}/deploy", response_model=VisualDesignResponse)
async def deploy_design(design_id: int, request: VisualDesignDeployRequest):
    """Deploy a visual design as a registered agent."""
    from app.services.code_generator import generate_agent_code
    
    try:
        # Get the design
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT name, graph_json, symbol, primary_timespan, primary_multiplier
                    FROM visual_agent_designs
                    WHERE id = %s
                    """,
                    (design_id,)
                )
                row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Design {design_id} not found")
        
        design_name = row[0]
        graph_json = row[1] if isinstance(row[1], dict) else json.loads(row[1]) if row[1] else {}
        
        # Generate code
        result = generate_agent_code(
            graph=graph_json,
            symbol=row[2],
            primary_timespan=row[3],
            primary_multiplier=row[4],
        )
        
        if result.errors:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot deploy: {'; '.join(result.errors)}"
            )
        
        # Register as agent
        agent_name = request.agent_name
        description = request.description or f"Visual design: {design_name}"
        path = f"db://agents/{agent_name}"
        
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                # Create/update agent
                cur.execute(
                    """
                    INSERT INTO agents_registry (name, path, code, description, enabled)
                    VALUES (%s, %s, %s, %s, TRUE)
                    ON CONFLICT (name) DO UPDATE
                    SET path = EXCLUDED.path,
                        code = EXCLUDED.code,
                        description = EXCLUDED.description
                    """,
                    (agent_name, path, result.code, description)
                )
                
                # Update design with agent link and generated code
                cur.execute(
                    """
                    UPDATE visual_agent_designs 
                    SET agent_name = %s, generated_code = %s
                    WHERE id = %s
                    RETURNING id, name, description, graph_json, symbol, 
                              primary_timespan, primary_multiplier, generated_code,
                              agent_name, created_at, updated_at
                    """,
                    (agent_name, result.code, design_id)
                )
                row = cur.fetchone()
            conn.commit()
        
        return VisualDesignResponse(
            id=row[0],
            name=row[1],
            description=row[2],
            graph_json=row[3] if isinstance(row[3], dict) else json.loads(row[3]) if row[3] else {},
            symbol=row[4],
            primary_timespan=row[5],
            primary_multiplier=row[6],
            generated_code=row[7],
            agent_name=row[8],
            created_at=str(row[9]) if row[9] else None,
            updated_at=str(row[10]) if row[10] else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Signal Preview (for sparklines)
# ============================================================================

@router.post("/signal-preview", response_model=SignalPreviewResponse)
async def get_signal_preview(request: SignalPreviewRequest):
    """Get preview data for a signal (for sparkline visualization)."""
    import os
    import sys
    
    # Ensure project root is in path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    from Common.massive_client import get_aggregate_bars
    from datetime import datetime, timedelta
    
    try:
        # Get signal spec from database
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT source, spec FROM available_signals WHERE id = %s",
                    (request.signal_id,)
                )
                row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Signal '{request.signal_id}' not found")
        
        source, spec = row
        
        if source == "massive":
            # Parse spec: SYMBOL:timespan:multiplier[:field]
            parts = spec.split(":")
            symbol = parts[0]
            timespan = parts[1] if len(parts) > 1 else "day"
            multiplier = int(parts[2]) if len(parts) > 2 else 1
            field = parts[3] if len(parts) > 3 else "close"
            
            # Get recent data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # Last 30 days
            
            df = get_aggregate_bars(
                symbol=symbol,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                timespan=timespan,
                multiplier=multiplier,
            )
            
            if df is None or df.empty:
                return SignalPreviewResponse(
                    signal_id=request.signal_id,
                    values=[],
                    timestamps=[],
                    min_val=0,
                    max_val=0,
                )
            
            # Get the last N points
            df = df.tail(request.num_points)
            values = df[field].astype(float).tolist()
            timestamps = df["time"].astype(str).tolist()
            
            return SignalPreviewResponse(
                signal_id=request.signal_id,
                values=values,
                timestamps=timestamps,
                min_val=min(values) if values else 0,
                max_val=max(values) if values else 0,
            )
        else:
            # For SF1 data, return empty for now (would need different fetching)
            return SignalPreviewResponse(
                signal_id=request.signal_id,
                values=[],
                timestamps=[],
                min_val=0,
                max_val=0,
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Templates
# ============================================================================

@router.get("/templates/list")
async def list_templates():
    """List available design templates."""
    from app.services.design_templates import get_templates
    return get_templates()


@router.post("/templates/{template_name}", response_model=VisualDesignResponse)
async def create_from_template(template_name: str, design_name: str):
    """Create a new design from a template."""
    from app.services.design_templates import get_template
    
    template = get_template(template_name)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
    
    # Create a new design based on the template
    design = VisualDesignCreate(
        name=design_name,
        description=template.get("description", f"Created from {template_name} template"),
        graph_json=template.get("graph", {}),
        symbol=template.get("symbol", "AAPL"),
        primary_timespan=template.get("primary_timespan", "day"),
        primary_multiplier=template.get("primary_multiplier", 1),
    )
    
    return await create_design(design)
