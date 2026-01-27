"""Signals API router."""

from typing import List
from fastapi import APIRouter, HTTPException

from Common.db import get_pg_conn
from app.models.schemas import SignalCreate, SignalResponse

router = APIRouter()


@router.get("", response_model=List[SignalResponse])
async def list_signals():
    """List all signals."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, source, spec, model_freq, description, enabled
                    FROM available_signals
                    ORDER BY id
                    """
                )
                rows = cur.fetchall()
        
        return [
            SignalResponse(
                id=row[0],
                source=row[1],
                spec=row[2],
                model_freq=row[3],
                description=row[4],
                enabled=row[5]
            )
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(signal_id: str):
    """Get a specific signal by ID."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, source, spec, model_freq, description, enabled
                    FROM available_signals
                    WHERE id = %s
                    """,
                    (signal_id,)
                )
                row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Signal '{signal_id}' not found")
        
        return SignalResponse(
            id=row[0],
            source=row[1],
            spec=row[2],
            model_freq=row[3],
            description=row[4],
            enabled=row[5]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=SignalResponse)
async def create_signal(signal: SignalCreate):
    """Create or update a signal."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO available_signals (id, source, spec, model_freq, description, enabled)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET source = EXCLUDED.source,
                        spec = EXCLUDED.spec,
                        model_freq = EXCLUDED.model_freq,
                        description = EXCLUDED.description,
                        enabled = EXCLUDED.enabled
                    """,
                    (signal.id, signal.source, signal.spec, signal.model_freq, 
                     signal.description, signal.enabled)
                )
            conn.commit()
        
        return signal
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{signal_id}")
async def delete_signal(signal_id: str):
    """Delete a signal."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM available_signals WHERE id = %s",
                    (signal_id,)
                )
            conn.commit()
        
        return {"message": f"Signal '{signal_id}' deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{signal_id}/toggle")
async def toggle_signal(signal_id: str):
    """Toggle signal enabled status."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE available_signals
                    SET enabled = NOT enabled
                    WHERE id = %s
                    RETURNING enabled
                    """,
                    (signal_id,)
                )
                result = cur.fetchone()
            conn.commit()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Signal '{signal_id}' not found")
        
        return {"id": signal_id, "enabled": result[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
