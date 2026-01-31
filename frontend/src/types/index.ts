// API Types

export interface Signal {
  id: string;
  source: 'massive' | 'sf1';
  spec: string;
  model_freq?: string;
  description?: string;
  enabled: boolean;
}

export interface TestDefinition {
  name: string;
  trials: number;
  overall_start_date: string;
  overall_end_date: string;
  seed?: number;
  record_curves: boolean;
  plot_dir?: string;
  trading_days: number;
}

export interface Job {
  test_name: string;
  agent_name: string;
}

export interface Agent {
  name: string;
  path: string;
  code?: string;
  description?: string;
  enabled: boolean;
  visual_design_id?: number;  // ID of linked visual design, if any
}

// Simulation Types

export interface BarData {
  timestamp: number;
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TradeEvent {
  timestamp: number;
  action: 'BUY' | 'SELL';
  quantity: number;
  price: number;
}

export interface SimulationUpdate {
  type: 'bar_update';
  job_id: string;
  job_index: number;
  test_name: string;
  agent_name: string;
  bar_index: number;
  bar: BarData;
  equity: number;
  position: number;
  cash: number;
  signals?: Record<string, number>;
}

export interface JobStatus {
  job_id: string;
  job_index: number;
  test_name: string;
  agent_name: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  progress_message?: string;
  progress_percent?: number;
  bars: BarData[];
  trades: TradeEvent[];
  equity_curve: { time: string; equity: number }[];
  final_result?: {
    success?: boolean;
    error?: string;
    final_equity?: number;
    total_bars?: number;
    execution_time_seconds?: number;
    data_load_time_seconds?: number;
    simulation_time_seconds?: number;
    chart_frequency?: {
      timespan: string;
      multiplier: number;
    };
    signal_ids?: string[];
    symbol?: string;
    all_bars?: any[];
  };
}

export interface SimulationState {
  session_id?: string;
  status: 'idle' | 'running' | 'completed' | 'error';
  jobs: JobStatus[];
  activeJobIndex: number;
  error?: string;
}

// WebSocket Message Types

export type WSMessage = 
  | { type: 'status'; status: string; jobs_total?: number; jobs_completed?: number }
  | { type: 'job_start'; job_id: string; job_index: number; test_name: string; agent_name: string }
  | SimulationUpdate
  | { type: 'job_complete'; job_id: string; job_index: number; test_name: string; agent_name: string; result: any }
  | { type: 'progress'; job_id: string; job_index: number; message: string; percent: number }
  | { type: 'error'; message: string }
  | { type: 'pong' };

// ============================================================================
// Visual Agent Designer Types
// ============================================================================

export interface VisualDesignNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, any>;
}

export interface VisualDesignEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}

export interface VisualDesignViewport {
  x: number;
  y: number;
  zoom: number;
}

export interface VisualDesignGraph {
  nodes: VisualDesignNode[];
  edges: VisualDesignEdge[];
  viewport: VisualDesignViewport;
}

export interface VisualDesign {
  id: number;
  name: string;
  description?: string;
  graph_json: VisualDesignGraph;
  symbol: string;
  primary_timespan: string;
  primary_multiplier: number;
  generated_code?: string;
  agent_name?: string;
  created_at?: string;
  updated_at?: string;
}

export interface VisualDesignCreate {
  name: string;
  description?: string;
  graph_json?: VisualDesignGraph;
  symbol?: string;
  primary_timespan?: string;
  primary_multiplier?: number;
}

export interface CodeGenerationResult {
  code: string;
  errors: string[];
  warnings: string[];
}

export interface ValidationError {
  node_id: string | null;
  message: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
  node_dimensions: Record<string, { inputs: Record<string, any>; output: any[] }>;
}

export interface SignalPreview {
  signal_id: string;
  values: number[];
  timestamps: string[];
  min_val: number;
  max_val: number;
}

export interface DesignTemplate {
  name: string;
  title: string;
  description: string;
  symbol: string;
  timespan: string;
}

// Node type definitions for the visual designer
export type VisualNodeType = 
  // Data Sources
  | 'signal'
  | 'constant'
  | 'variable'
  | 'range'
  // 1-D Transformations
  | 'slice'
  | 'add'
  | 'subtract'
  | 'multiply'
  | 'divide'
  | 'normalize'
  | 'clip'
  | 'rolling_mean'
  | 'rolling_std'
  | 'shift'
  | 'shift_diff'
  | 'conv1d_custom'
  | 'sign'
  | 'sin'
  | 'cos'
  // Data Sources
  | 'agent_state'
  | 'agent_equity_curve'
  | 'custom_state'
  | 'rsi'
  | 'macd'
  | 'bollinger'
  // Aggregation
  | 'sum'
  | 'mean'
  | 'std'
  | 'variance'
  | 'min'
  | 'max'
  // Multi-dimension Transforms
  | 'concat'
  | 'transpose'
  | 'matmul'
  // ML Layers
  | 'linear'
  | 'relu'
  | 'tanh'
  | 'sigmoid'
  | 'softmax'
  | 'lstm'
  | 'conv1d'
  // Output
  | 'output';

export interface NodeTypeDefinition {
  type: VisualNodeType;
  label: string;
  category: 'data' | 'transform1d' | 'aggregation' | 'transformNd' | 'ml' | 'output';
  inputs: { name: string; type: string }[];
  outputs: { name: string; type: string }[];
  defaultData: Record<string, any>;
  color: string;
}
