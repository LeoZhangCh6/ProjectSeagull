import { create } from 'zustand';
import type { SimulationState, JobStatus, BarData, TradeEvent, WSMessage } from '../types';

interface SimulationStore extends SimulationState {
  // Actions
  setSessionId: (id: string) => void;
  setStatus: (status: SimulationState['status']) => void;
  setError: (error: string) => void;
  setActiveJobIndex: (index: number) => void;
  nextJob: () => void;
  prevJob: () => void;
  
  // Job management
  initJob: (jobId: string, jobIndex: number, testName: string, agentName: string) => void;
  updateJob: (jobIndex: number, bar: BarData, equity: number, position: number, cash: number) => void;
  completeJob: (jobIndex: number, result: JobStatus['final_result']) => void;
  addTrade: (jobIndex: number, trade: TradeEvent) => void;
  
  // Handle WebSocket messages
  handleMessage: (message: WSMessage) => void;
  
  // Reset
  reset: () => void;
}

const initialState: SimulationState = {
  session_id: undefined,
  status: 'idle',
  jobs: [],
  activeJobIndex: 0,
  error: undefined,
};

export const useSimulationStore = create<SimulationStore>((set, get) => ({
  ...initialState,
  
  setSessionId: (id) => set({ session_id: id }),
  
  setStatus: (status) => set({ status }),
  
  setError: (error) => set({ error, status: 'error' }),
  
  setActiveJobIndex: (index) => {
    const { jobs } = get();
    if (index >= 0 && index < jobs.length) {
      set({ activeJobIndex: index });
    }
  },
  
  nextJob: () => {
    const { activeJobIndex, jobs } = get();
    if (activeJobIndex < jobs.length - 1) {
      set({ activeJobIndex: activeJobIndex + 1 });
    }
  },
  
  prevJob: () => {
    const { activeJobIndex } = get();
    if (activeJobIndex > 0) {
      set({ activeJobIndex: activeJobIndex - 1 });
    }
  },
  
  initJob: (jobId, jobIndex, testName, agentName) => {
    set((state) => {
      const jobs = [...state.jobs];
      // Initialize as 'pending' - will change to 'running' when first progress update arrives
      jobs[jobIndex] = {
        job_id: jobId,
        job_index: jobIndex,
        test_name: testName,
        agent_name: agentName,
        status: 'pending',
        progress_message: 'Queued...',
        progress_percent: 0,
        bars: [],
        trades: [],
        equity_curve: [],
      };
      return { jobs };
    });
  },
  
  updateJob: (jobIndex, bar, equity, position, cash) => {
    set((state) => {
      const jobs = [...state.jobs];
      if (jobs[jobIndex]) {
        const prevCurve = jobs[jobIndex].equity_curve;
        const curvePoint: { time: string; equity: number; position?: number; cash?: number; close?: number } = {
          time: bar?.time ?? (prevCurve.length ? prevCurve[prevCurve.length - 1].time : ''),
          equity,
          position,
          cash,
          close: bar?.close,
        };
        jobs[jobIndex] = {
          ...jobs[jobIndex],
          bars: bar ? [...jobs[jobIndex].bars, bar] : jobs[jobIndex].bars,
          equity_curve: [...prevCurve, curvePoint],
        };
      }
      return { jobs };
    });
  },
  
  completeJob: (jobIndex, result) => {
    set((state) => {
      const jobs = [...state.jobs];
      if (jobs[jobIndex]) {
        const job = jobs[jobIndex];
        // Use portfolio_curve from result when available (has position, cash, close per bar)
        const equity_curve = result?.portfolio_curve?.length
          ? result.portfolio_curve.map((p: { time: string; equity: number; position: number; cash: number; close: number }) => ({
              time: p.time, equity: p.equity, position: p.position, cash: p.cash, close: p.close,
            }))
          : job.equity_curve;
        jobs[jobIndex] = {
          ...job,
          status: result?.error ? 'error' : 'completed',
          final_result: result,
          bars: result?.all_bars || job.bars,
          trades: result?.trades ?? job.trades,
          equity_curve,
        };
      }
      return { jobs };
    });
  },
  
  addTrade: (jobIndex, trade) => {
    set((state) => {
      const jobs = [...state.jobs];
      if (jobs[jobIndex]) {
        jobs[jobIndex] = {
          ...jobs[jobIndex],
          trades: [...jobs[jobIndex].trades, trade],
        };
      }
      return { jobs };
    });
  },
  
  handleMessage: (message) => {
    const store = get();
    
    switch (message.type) {
      case 'status':
        if (message.status === 'started') {
          set({ status: 'running' });
        } else if (message.status === 'completed') {
          set({ status: 'completed' });
        }
        break;
        
      case 'job_start':
        store.initJob(message.job_id, message.job_index, message.test_name, message.agent_name);
        break;
        
      case 'progress':
        set((state) => {
          const jobs = [...state.jobs];
          if (jobs[message.job_index]) {
            jobs[message.job_index] = {
              ...jobs[message.job_index],
              status: 'running',  // Mark as running once we get progress
              progress_message: message.message,
              progress_percent: message.percent,
            };
          }
          return { jobs };
        });
        break;
        
      case 'bar_update':
        store.updateJob(
          message.job_index,
          message.bar,
          message.equity,
          message.position,
          message.cash
        );
        break;
        
      case 'job_complete':
        store.completeJob(message.job_index, message.result);
        break;
        
      case 'error':
        store.setError(message.message);
        break;
    }
  },
  
  reset: () => set(initialState),
}));
