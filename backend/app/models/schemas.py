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
    visual_design_id: Optional[int] = None  # ID of linked visual design, if any
    
    class Config:
        from_attributes = True


class AgentClone(BaseModel):
    source_name: str
    new_name: str


class AgentRename(BaseModel):
    new_name: str


# Test Definition Update schema (partial update)
class TestDefinitionUpdate(BaseModel):
    name: Optional[str] = None
    trials: Optional[int] = None
    overall_start_date: Optional[date] = None
    overall_end_date: Optional[date] = None
    seed: Optional[int] = None
    record_curves: Optional[bool] = None
    plot_dir: Optional[str] = None
    trading_days: Optional[int] = None


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


# ============================================================================
# Visual Agent Designer schemas
# ============================================================================

class VisualDesignNode(BaseModel):
    """A single node in the visual design graph."""
    id: str
    type: str  # "signal", "variable", "operation", "output", "constant", etc.
    position: dict  # {"x": float, "y": float}
    data: dict  # Node-specific data (label, config, etc.)


class VisualDesignEdge(BaseModel):
    """A connection between two nodes."""
    id: str
    source: str  # Source node ID
    target: str  # Target node ID
    sourceHandle: Optional[str] = None  # Which output port
    targetHandle: Optional[str] = None  # Which input port


class VisualDesignViewport(BaseModel):
    """Canvas viewport state."""
    x: float = 0
    y: float = 0
    zoom: float = 1


class VisualDesignGraph(BaseModel):
    """The complete graph structure."""
    nodes: List[VisualDesignNode] = []
    edges: List[VisualDesignEdge] = []
    viewport: VisualDesignViewport = VisualDesignViewport()


class VisualDesignBase(BaseModel):
    """Base visual design model."""
    name: str
    description: Optional[str] = None
    graph_json: VisualDesignGraph = VisualDesignGraph()
    symbol: str = "AAPL"
    primary_timespan: str = "day"
    primary_multiplier: int = 1


class VisualDesignCreate(VisualDesignBase):
    """Create a new visual design."""
    pass


class VisualDesignUpdate(BaseModel):
    """Update an existing visual design (partial)."""
    name: Optional[str] = None
    description: Optional[str] = None
    graph_json: Optional[VisualDesignGraph] = None
    symbol: Optional[str] = None
    primary_timespan: Optional[str] = None
    primary_multiplier: Optional[int] = None


class VisualDesignResponse(VisualDesignBase):
    """Response model for visual design."""
    id: int
    generated_code: Optional[str] = None
    agent_name: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class VisualDesignDeployRequest(BaseModel):
    """Request to deploy a visual design as an agent."""
    agent_name: str
    description: Optional[str] = None


class CodeGenerationRequest(BaseModel):
    """Request to generate code from a graph."""
    graph_json: VisualDesignGraph
    symbol: str = "AAPL"
    primary_timespan: str = "day"
    primary_multiplier: int = 1


class CodeGenerationResponse(BaseModel):
    """Response with generated Python code."""
    code: str
    errors: List[str] = []
    warnings: List[str] = []


class ValidationResult(BaseModel):
    """Result of graph validation."""
    valid: bool
    errors: List[dict] = []  # {"node_id": str, "message": str}
    warnings: List[dict] = []
    node_dimensions: dict = {}  # {"node_id": {"output": [dim1, dim2, ...]}}


class SignalPreviewRequest(BaseModel):
    """Request signal preview data for sparklines."""
    signal_id: str
    num_points: int = 20


class SignalPreviewResponse(BaseModel):
    """Response with signal preview data."""
    signal_id: str
    values: List[float]
    timestamps: List[str]
    min_val: float
    max_val: float
