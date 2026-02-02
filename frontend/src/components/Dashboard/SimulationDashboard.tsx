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
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [reconnectedAt, setReconnectedAt] = useState<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const hasStartedRef = useRef(false);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const reconnectAttemptsRef = useRef(0);
  const isMountedRef = useRef(true);
  
  const MAX_RECONNECT_ATTEMPTS = 5;
  const RECONNECT_BASE_DELAY_MS = 2000;
  
  // WebSocket connection with auto-reconnect on unexpected disconnect
  useEffect(() => {
    if (!session_id) return;
    
    isMountedRef.current = true;
    hasStartedRef.current = false;
    reconnectAttemptsRef.current = 0;
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/simulation/${session_id}`;
    
    const connect = () => {
      if (!isMountedRef.current) return;
      
      console.log('[Dashboard] Connecting to:', wsUrl, reconnectAttemptsRef.current > 0 ? `(attempt ${reconnectAttemptsRef.current + 1})` : '');
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      
      ws.onopen = () => {
        if (!isMountedRef.current) {
          ws.close();
          return;
        }
        const wasReconnect = reconnectAttemptsRef.current > 0;
        reconnectAttemptsRef.current = 0;
        setIsReconnecting(false);
        console.log('[Dashboard] WebSocket connected');
        setIsConnected(true);
        
        if (!hasStartedRef.current) {
          hasStartedRef.current = true;
          console.log('[Dashboard] Sending start action');
          ws.send(JSON.stringify({ action: 'start' }));
          setStatus('running');
        } else if (wasReconnect) {
          setReconnectedAt(Date.now());
          setTimeout(() => setReconnectedAt(null), 4000);
        }
      };
      
      ws.onclose = (event) => {
        wsRef.current = null;
        setIsConnected(false);
        if (!isMountedRef.current) return;
        
        // 1000 = normal closure (e.g. server finished, user navigated away)
        if (event.code === 1000) return;
        
        if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
          console.log('[Dashboard] Max reconnect attempts reached, giving up');
          setIsReconnecting(false);
          return;
        }
        
        setIsReconnecting(true);
        const delay = Math.min(RECONNECT_BASE_DELAY_MS * Math.pow(2, reconnectAttemptsRef.current), 30000);
        reconnectAttemptsRef.current += 1;
        console.log(`[Dashboard] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
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
    };
    
    connect();
    
    return () => {
      isMountedRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = undefined;
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      console.log('[Dashboard] WebSocket cleanup');
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
  
  // Trades: prefer final_result.trades (from job_complete) since backend sends full list on completion
  const trades = activeJob?.final_result?.trades ?? activeJob?.trades ?? [];
  const tradesCount = trades.length;
  
  // Trade duration: (1) During simulation: timestamp diff → days. (2) After completion: bar count × frequency → days.
  const bars = activeJob?.bars ?? [];
  const chartFreq = activeJob?.final_result?.chart_frequency;
  let tradeDurationDays: number | null = null;
  
  const timestampToDays = (diff: number): number => {
    if (diff <= 0) return 0;
    // Detect ms vs seconds: if diff > ~100 days in seconds (8.64e6), assume ms
    const msPerDay = 86400000;
    const secPerDay = 86400;
    const days = diff > secPerDay * 100 ? diff / msPerDay : diff / secPerDay;
    return Math.round(days);
  };
  
  if (bars.length >= 2) {
    if (chartFreq) {
      const ts = (chartFreq.timespan || '').toLowerCase();
      const mult = chartFreq.multiplier ?? 1;
      if (ts === 'day') {
        tradeDurationDays = Math.round(bars.length * mult);
      } else if (ts === 'hour') {
        tradeDurationDays = Math.round((bars.length * mult) / 24);
      } else if (ts === 'minute' || ts === 'min') {
        tradeDurationDays = Math.round((bars.length * mult) / (60 * 24));
      } else {
        const diff = bars[bars.length - 1].timestamp - bars[0].timestamp;
        tradeDurationDays = timestampToDays(diff);
      }
    } else {
      // During simulation: use (last_timestamp - first_timestamp) converted to days
      const diff = bars[bars.length - 1].timestamp - bars[0].timestamp;
      tradeDurationDays = timestampToDays(diff);
    }
  }
  
  // Underlying stock return: (last_close - first_close) / first_close * 100
  const underlyingReturnPercent = bars.length >= 2 && bars[0].close > 0
    ? ((bars[bars.length - 1].close - bars[0].close) / bars[0].close) * 100
    : null;

  // Curve data with position & ratio for new charts (use equity_curve which has position/close from portfolio_curve)
  const curve = activeJob?.equity_curve ?? [];
  const positionData = curve.map(p => ({ time: p.time, position: p.position ?? 0 }));
  const ratioData = curve
    .filter(p => (p.equity ?? 0) > 0 && p.close != null)
    .map(p => ({
      time: p.time,
      ratio: ((p.position ?? 0) * (p.close ?? 0) / (p.equity ?? 1)) * 100,
    }));
  
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
      
      {/* Connection restored toast */}
      {reconnectedAt && (
        <div className="mx-4 mt-2 px-4 py-2 bg-green-900/50 border border-green-600 rounded text-green-200 text-sm">
          Connection restored. Simulation may have been interrupted — run again from Config if needed.
        </div>
      )}
      
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
              <div className="grid grid-cols-6 gap-4">
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
                  label="Trade Duration" 
                  value={tradeDurationDays !== null ? `${tradeDurationDays} days` : '–'}
                />
                <MetricCard 
                  label="Underlying Return" 
                  value={underlyingReturnPercent !== null 
                    ? `${underlyingReturnPercent >= 0 ? '+' : ''}${underlyingReturnPercent.toFixed(2)}%` 
                    : '–'}
                  color={underlyingReturnPercent !== null 
                    ? (underlyingReturnPercent >= 0 ? 'text-green-400' : 'text-red-400') 
                    : undefined}
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
                  <CandlestickChart data={activeJob.bars} />
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
              
              {/* Position (shares held) over time */}
              {positionData.length > 0 && (
                <div className="card p-4">
                  <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-3">
                    Position (shares held)
                  </h3>
                  <div className="h-[160px]">
                    <LineChart 
                      data={positionData}
                      dataKey="position"
                      color="#A78BFA"
                      name="Shares"
                    />
                  </div>
                </div>
              )}
              
              {/* Stock value / total equity ratio (%) */}
              {ratioData.length > 0 && (
                <div className="card p-4">
                  <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-3">
                    Stock / Equity (%)
                  </h3>
                  <div className="h-[160px]">
                    <LineChart 
                      data={ratioData}
                      dataKey="ratio"
                      color="#F59E0B"
                      name="Stock/Equity %"
                    />
                  </div>
                </div>
              )}
              
              {/* Trades Table */}
              {trades.length > 0 && (
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
                        {trades.slice(-10).reverse().map((trade, i) => (
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
                    <div className="text-red-400">
                      <pre className="whitespace-pre-wrap text-sm font-mono bg-red-500/10 p-3 rounded max-h-64 overflow-y-auto">
                        {activeJob.final_result.error || 'Unknown error occurred. Check server logs for details.'}
                      </pre>
                    </div>
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
                  <div className="text-yellow-400 text-sm">
                    {isReconnecting ? 'Reconnecting...' : 'Connecting to server...'}
                  </div>
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
