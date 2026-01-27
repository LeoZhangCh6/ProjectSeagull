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
      jobs[jobIndex] = {
        job_id: jobId,
        job_index: jobIndex,
        test_name: testName,
        agent_name: agentName,
        status: 'running',
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
        jobs[jobIndex] = {
          ...jobs[jobIndex],
          bars: [...jobs[jobIndex].bars, bar],
          equity_curve: [...jobs[jobIndex].equity_curve, { time: bar.time, equity }],
        };
      }
      return { jobs };
    });
  },
  
  completeJob: (jobIndex, result) => {
    set((state) => {
      const jobs = [...state.jobs];
      if (jobs[jobIndex]) {
        jobs[jobIndex] = {
          ...jobs[jobIndex],
          status: result?.error ? 'error' : 'completed',
          final_result: result,
          // If result includes all_bars, replace bars array with complete data
          bars: result?.all_bars || jobs[jobIndex].bars,
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
