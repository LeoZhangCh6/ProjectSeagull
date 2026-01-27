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
