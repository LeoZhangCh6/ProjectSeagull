"""Test Definitions API router."""

from typing import List
from fastapi import APIRouter, HTTPException

from Common.db import get_pg_conn
from app.models.schemas import TestDefinitionCreate, TestDefinitionResponse

router = APIRouter()


@router.get("", response_model=List[TestDefinitionResponse])
async def list_tests():
    """List all test definitions."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT name, trials, overall_start_date, overall_end_date,
                           seed, record_curves, plot_dir, trading_days
                    FROM test_definitions
                    ORDER BY name
                    """
                )
                rows = cur.fetchall()
        
        return [
            TestDefinitionResponse(
                name=row[0],
                trials=row[1],
                overall_start_date=row[2],
                overall_end_date=row[3],
                seed=row[4],
                record_curves=row[5],
                plot_dir=row[6],
                trading_days=row[7]
            )
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{test_name}", response_model=TestDefinitionResponse)
async def get_test(test_name: str):
    """Get a specific test definition."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT name, trials, overall_start_date, overall_end_date,
                           seed, record_curves, plot_dir, trading_days
                    FROM test_definitions
                    WHERE name = %s
                    """,
                    (test_name,)
                )
                row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Test '{test_name}' not found")
        
        return TestDefinitionResponse(
            name=row[0],
            trials=row[1],
            overall_start_date=row[2],
            overall_end_date=row[3],
            seed=row[4],
            record_curves=row[5],
            plot_dir=row[6],
            trading_days=row[7]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=TestDefinitionResponse)
async def create_test(test: TestDefinitionCreate):
    """Create or update a test definition."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO test_definitions 
                    (name, trials, overall_start_date, overall_end_date, seed, 
                     record_curves, plot_dir, trading_days)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE
                    SET trials = EXCLUDED.trials,
                        overall_start_date = EXCLUDED.overall_start_date,
                        overall_end_date = EXCLUDED.overall_end_date,
                        seed = EXCLUDED.seed,
                        record_curves = EXCLUDED.record_curves,
                        plot_dir = EXCLUDED.plot_dir,
                        trading_days = EXCLUDED.trading_days
                    """,
                    (test.name, test.trials, test.overall_start_date, test.overall_end_date,
                     test.seed, test.record_curves, test.plot_dir, test.trading_days)
                )
            conn.commit()
        
        return test
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{test_name}")
async def delete_test(test_name: str):
    """Delete a test definition."""
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM test_definitions WHERE name = %s",
                    (test_name,)
                )
            conn.commit()
        
        return {"message": f"Test '{test_name}' deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
