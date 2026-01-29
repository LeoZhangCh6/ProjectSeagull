import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ChevronLeft, ChevronRight, Square } from 'lucide-react';
import { useSimulationStore } from '../../stores/simulationStore';
import { CandlestickChart } from '../Charts/CandlestickChart';
import { LineChart } from '../Charts/LineChart';
import { JobList } from '../Navigation/JobList';

interface SimulationDashboardProps {
  onBack: () => void;
}

export function SimulationDashboard({ onBack }: SimulationDashboardProps) {
  const { 
    status, 
    jobs, 
    activeJobIndex,
    session_id,
    setActiveJobIndex,
    nextJob,
    prevJob,
    reset,
    handleMessage,
    setStatus,
  } = useSimulationStore();
  
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const hasStartedRef = useRef(false);
  
  // WebSocket connection - managed directly to avoid closure issues
  useEffect(() => {
    if (!session_id) return;
    
    // Reset started flag for new session
    hasStartedRef.current = false;
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/simulation/${session_id}`;
    
    console.log('[Dashboard] Connecting to:', wsUrl);
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    
    ws.onopen = () => {
      console.log('[Dashboard] WebSocket connected');
      setIsConnected(true);
      
      // Send start message immediately
      if (!hasStartedRef.current) {
        hasStartedRef.current = true;
        console.log('[Dashboard] Sending start action');
        ws.send(JSON.stringify({ action: 'start' }));
        setStatus('running');
      }
    };
    
    ws.onclose = (event) => {
      console.log('[Dashboard] WebSocket closed:', event.code, event.reason);
      setIsConnected(false);
      wsRef.current = null;
    };
    
    ws.onerror = (error) => {
      console.error('[Dashboard] WebSocket error:', error);
    };
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('[Dashboard] Received:', message.type);
        handleMessage(message);
      } catch (e) {
        console.error('[Dashboard] Failed to parse message:', e);
      }
    };
    
    return () => {
      console.log('[Dashboard] Cleaning up WebSocket');
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
      wsRef.current = null;
    };
  }, [session_id, handleMessage, setStatus]);
  
  const activeJob = jobs[activeJobIndex];
  
  const handleStop = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'stop' }));
    }
    reset();
    onBack();
  };
  
  const handleBack = () => {
    if (status === 'running') {
      if (confirm('Simulation is still running. Stop and go back?')) {
        handleStop();
      }
    } else {
      reset();
      onBack();
    }
  };
  
  // Calculate metrics for active job
  const currentEquity = activeJob?.equity_curve.length 
    ? activeJob.equity_curve[activeJob.equity_curve.length - 1].equity 
    : 100000;
  const startEquity = 100000;
  const pnl = currentEquity - startEquity;
  const pnlPercent = ((currentEquity / startEquity) - 1) * 100;
  const tradesCount = activeJob?.trades.length ?? 0;
  
  return (
    <div className="h-[calc(100vh-73px)] flex flex-col">
      {/* Dashboard Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-color)] bg-[var(--bg-secondary)]">
        <div className="flex items-center gap-4">
          <button onClick={handleBack} className="btn btn-secondary flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          
          <div className="flex items-center gap-2">
            <span className={`inline-block w-3 h-3 rounded-full ${
              status === 'running' ? 'bg-green-500 animate-pulse' :
              status === 'completed' ? 'bg-blue-500' :
              status === 'error' ? 'bg-red-500' : 'bg-gray-500'
            }`} />
            <span className="text-sm capitalize">{status}</span>
            {isConnected && <span className="text-xs text-green-400">(connected)</span>}
          </div>
          
          <span className="text-sm text-[var(--text-secondary)]">
            {jobs.length} job{jobs.length !== 1 ? 's' : ''}
          </span>
        </div>
        
        {/* Job Navigation */}
        <div className="flex items-center gap-4">
          <button 
            onClick={prevJob} 
            disabled={activeJobIndex === 0}
            className="btn btn-secondary p-2 disabled:opacity-50"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          
          <span className="min-w-[120px] text-center font-medium">
            {activeJob ? `${activeJob.test_name} / ${activeJob.agent_name}` : 'No job selected'}
          </span>
          
          <button 
            onClick={nextJob} 
            disabled={activeJobIndex >= jobs.length - 1}
            className="btn btn-secondary p-2 disabled:opacity-50"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
          
          {status === 'running' && (
            <button onClick={handleStop} className="btn btn-danger flex items-center gap-2">
              <Square className="w-4 h-4" />
              Stop
            </button>
          )}
        </div>
      </div>
      
      {/* Main Dashboard Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Job List Sidebar */}
        <div className="w-64 border-r border-[var(--border-color)] overflow-y-auto bg-[var(--bg-secondary)]">
          {/* Overall Progress Summary */}
          {status === 'running' && jobs.length > 1 && (
            <div className="p-4 border-b border-[var(--border-color)] bg-[var(--bg-tertiary)]">
              <div className="text-sm font-medium mb-2">Overall Progress</div>
              <div className="flex gap-2 text-xs mb-2">
                <span className="text-yellow-400">
                  {jobs.filter(j => j.status === 'pending').length} queued
                </span>
                <span className="text-blue-400">
                  {jobs.filter(j => j.status === 'running').length} running
                </span>
                <span className="text-green-400">
                  {jobs.filter(j => j.status === 'completed').length} done
                </span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-green-500 h-2 rounded-full transition-all duration-300" 
                  style={{ 
                    width: `${(jobs.filter(j => j.status === 'completed').length / jobs.length) * 100}%` 
                  }}
                />
              </div>
            </div>
          )}
          
          <JobList 
            jobs={jobs} 
            activeIndex={activeJobIndex} 
            onSelect={setActiveJobIndex} 
          />
        </div>
        
        {/* Charts Area */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeJob ? (
            <div className="space-y-4">
              {/* Job Info */}
              {activeJob.final_result?.chart_frequency && (
                <div className="card p-3 bg-[var(--bg-secondary)]">
                  <div className="text-sm text-[var(--text-secondary)] flex flex-wrap gap-x-4">
                    <span>
                      <strong>Frequency:</strong> {activeJob.final_result.chart_frequency.timespan} × {activeJob.final_result.chart_frequency.multiplier}
                    </span>
                    {activeJob.final_result.signal_ids && activeJob.final_result.signal_ids.length > 0 && (
                      <span>
                        <strong>Signals:</strong> {activeJob.final_result.signal_ids.join(', ')}
                      </span>
                    )}
                  </div>
                </div>
              )}
              
              {/* Metrics Bar */}
              <div className="grid grid-cols-4 gap-4">
                <MetricCard 
                  label="Equity" 
                  value={`$${currentEquity.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                />
                <MetricCard 
                  label="P&L" 
                  value={`${pnl >= 0 ? '+' : ''}$${pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                  color={pnl >= 0 ? 'text-green-400' : 'text-red-400'}
                />
                <MetricCard 
                  label="Return" 
                  value={`${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(2)}%`}
                  color={pnlPercent >= 0 ? 'text-green-400' : 'text-red-400'}
                />
                <MetricCard 
                  label="Trades" 
                  value={tradesCount.toString()}
                />
              </div>
              
              {/* Candlestick Chart */}
              <div className="card p-4">
                <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-3">
                  {activeJob.final_result?.symbol || 'Price'} Chart ({activeJob.bars.length} bars)
                  {activeJob.final_result?.chart_frequency && (
                    <span className="ml-2">
                      - {activeJob.final_result.chart_frequency.timespan} × {activeJob.final_result.chart_frequency.multiplier}
                    </span>
                  )}
                </h3>
                <div className="h-[300px]">
                  <CandlestickChart 
                    data={activeJob.bars} 
                    trades={activeJob.trades}
                  />
                </div>
              </div>
              
              {/* Equity Curve */}
              <div className="card p-4">
                <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-3">
                  Equity Curve
                </h3>
                <div className="h-[200px]">
                  <LineChart 
                    data={activeJob.equity_curve}
                    dataKey="equity"
                    color="#00E5FF"
                    name="Equity"
                    referenceLine={100000}
                  />
                </div>
              </div>
              
              {/* Trades Table */}
              {activeJob.trades.length > 0 && (
                <div className="card p-4">
                  <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-3">
                    Recent Trades
                  </h3>
                  <div className="max-h-[200px] overflow-y-auto">
                    <table>
                      <thead>
                        <tr>
                          <th>Time</th>
                          <th>Action</th>
                          <th>Qty</th>
                          <th>Price</th>
                        </tr>
                      </thead>
                      <tbody>
                        {activeJob.trades.slice(-10).reverse().map((trade, i) => (
                          <tr key={i}>
                            <td className="font-mono text-sm">
                              {new Date(trade.timestamp).toLocaleTimeString()}
                            </td>
                            <td className={trade.action === 'BUY' ? 'text-green-400' : 'text-red-400'}>
                              {trade.action}
                            </td>
                            <td>{trade.quantity}</td>
                            <td>${trade.price.toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
              
              {/* Final Result */}
              {activeJob.final_result && (
                <div className={`card p-4 ${activeJob.final_result.error ? 'border-red-500' : 'border-green-500'} border`}>
                  <h3 className="text-sm font-medium mb-2">
                    {activeJob.final_result.error ? 'Error' : 'Completed'}
                  </h3>
                  {activeJob.final_result.error ? (
                    <p className="text-red-400">{activeJob.final_result.error}</p>
                  ) : (
                    <div className="text-sm text-[var(--text-secondary)]">
                      Final Equity: ${activeJob.final_result.final_equity?.toLocaleString()} | 
                      Total Bars: {activeJob.final_result.total_bars}
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-[var(--text-secondary)]">
              <div className="text-center">
                <div className="mb-2">
                  {status === 'idle' ? 'Start a simulation to see results' : 
                   status === 'running' ? 'Waiting for data...' : 
                   'No data available'}
                </div>
                {!isConnected && session_id && (
                  <div className="text-yellow-400 text-sm">Connecting to server...</div>
                )}
                {isConnected && status === 'running' && (
                  <div className="text-blue-400 text-sm">Simulation started, waiting for first job...</div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="card p-4">
      <div className="text-sm text-[var(--text-secondary)]">{label}</div>
      <div className={`text-xl font-bold ${color || ''}`}>{value}</div>
    </div>
  );
}
