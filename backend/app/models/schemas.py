"""Pydantic models for API request/response schemas."""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel


# Signal schemas
class SignalBase(BaseModel):
    id: str
    source: str  # "massive" | "sf1"
    spec: str
    model_freq: Optional[str] = None
    description: Optional[str] = None
    enabled: bool = True


class SignalCreate(SignalBase):
    pass


class SignalResponse(SignalBase):
    class Config:
        from_attributes = True


# Test Definition schemas
class TestDefinitionBase(BaseModel):
    name: str
    trials: int
    overall_start_date: date
    overall_end_date: date
    seed: Optional[int] = None
    record_curves: bool = False
    plot_dir: Optional[str] = None
    trading_days: int = 14


class TestDefinitionCreate(TestDefinitionBase):
    pass


class TestDefinitionResponse(TestDefinitionBase):
    class Config:
        from_attributes = True


# Job schemas
class JobBase(BaseModel):
    test_name: str
    agent_name: str


class JobCreate(JobBase):
    pass


class JobResponse(JobBase):
    class Config:
        from_attributes = True


# Agent schemas
class AgentBase(BaseModel):
    name: str
    path: str
    code: Optional[str] = None
    description: Optional[str] = None
    enabled: bool = True


class AgentCreate(AgentBase):
    pass


class AgentResponse(AgentBase):
    class Config:
        from_attributes = True


class AgentClone(BaseModel):
    source_name: str
    new_name: str


# Simulation schemas
class SimulationStart(BaseModel):
    job_ids: Optional[List[str]] = None  # If None, run all jobs
    test_names: Optional[List[str]] = None


class SimulationStatus(BaseModel):
    session_id: str
    status: str  # "running" | "completed" | "error"
    jobs_total: int
    jobs_completed: int
    current_job: Optional[str] = None


# WebSocket message schemas
class BarData(BaseModel):
    timestamp: int
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class TradeEvent(BaseModel):
    timestamp: int
    action: str  # "BUY" | "SELL"
    quantity: int
    price: float


class SimulationUpdate(BaseModel):
    job_id: str
    test_name: str
    agent_name: str
    bar_index: int
    bar: BarData
    signals: dict  # signal_id -> value
    equity: float
    position: int
    cash: float
    trades: List[TradeEvent] = []
