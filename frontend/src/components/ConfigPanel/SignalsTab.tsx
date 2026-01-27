import { useState, useEffect, useCallback } from 'react';
import { Trash2, Plus, RefreshCw, ToggleLeft, ToggleRight } from 'lucide-react';
import { signalsApi } from '../../api/client';
import type { Signal } from '../../types';

const SOURCES = ['massive', 'sf1'] as const;
const MASSIVE_TIMESPANS = ['minute', 'hour', 'day', 'week', 'month'];
const MASSIVE_FIELDS = ['open', 'high', 'low', 'close', 'volume', 'vwap'];
const SF1_DIMENSIONS = ['MRY', 'MRQ', 'MRT', 'ARY', 'ARQ', 'ART'];
const SF1_COLUMNS = ['revenue', 'assets', 'liabilities', 'equity', 'cashneq', 'debt', 
                    'fcf', 'grossprofit', 'netinc', 'eps', 'ebitda', 'marketcap',
                    'pb', 'pe', 'ps', 'roe', 'roa', 'de'];

export function SignalsTab() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form state
  const [source, setSource] = useState<'massive' | 'sf1'>('massive');
  const [symbol, setSymbol] = useState('');
  const [timespan, setTimespan] = useState('day');
  const [multiplier, setMultiplier] = useState(1);
  const [field, setField] = useState('close');
  const [dimension, setDimension] = useState('ARQ');
  const [column, setColumn] = useState('revenue');
  const [description, setDescription] = useState('');
  
  const loadSignals = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await signalsApi.list();
      setSignals(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load signals');
    } finally {
      setLoading(false);
    }
  }, []);
  
  useEffect(() => {
    loadSignals();
  }, [loadSignals]);
  
  const generateSignalId = () => {
    if (source === 'massive') {
      return `${symbol.toUpperCase()}_${timespan}_${field}`;
    } else {
      return `${symbol.toUpperCase()}_${dimension.toLowerCase()}_${column}`;
    }
  };
  
  const generateSpec = () => {
    if (source === 'massive') {
      return `${symbol.toUpperCase()}:${timespan}:${multiplier}:${field}`;
    } else {
      return `${symbol.toUpperCase()}:${dimension}:${column}`;
    }
  };
  
  const handleCreate = async () => {
    if (!symbol) {
      setError('Symbol is required');
      return;
    }
    
    const signal: Signal = {
      id: generateSignalId(),
      source,
      spec: generateSpec(),
      model_freq: '1D',
      description: description || `${symbol.toUpperCase()} ${source} signal`,
      enabled: true,
    };
    
    try {
      await signalsApi.create(signal);
      setSymbol('');
      setDescription('');
      await loadSignals();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create signal');
    }
  };
  
  const handleDelete = async (id: string) => {
    if (!confirm(`Delete signal "${id}"?`)) return;
    try {
      await signalsApi.delete(id);
      await loadSignals();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete signal');
    }
  };
  
  const handleToggle = async (id: string) => {
    try {
      await signalsApi.toggle(id);
      await loadSignals();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to toggle signal');
    }
  };
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Signal Management</h2>
        <button onClick={loadSignals} className="btn btn-secondary" disabled={loading}>
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>
      
      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-2 rounded">
          {error}
        </div>
      )}
      
      {/* Create Signal Form */}
      <div className="card p-4 bg-[var(--bg-tertiary)]">
        <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-3">Register Signal</h3>
        
        {/* Source Selection */}
        <div className="flex gap-4 mb-4">
          {SOURCES.map((s) => (
            <label key={s} className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="source"
                value={s}
                checked={source === s}
                onChange={() => setSource(s)}
              />
              <span className="capitalize">{s}</span>
            </label>
          ))}
        </div>
        
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Symbol *</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="w-full"
              placeholder="AAPL"
            />
          </div>
          
          {source === 'massive' ? (
            <>
              <div>
                <label className="block text-sm text-[var(--text-secondary)] mb-1">Timespan</label>
                <select value={timespan} onChange={(e) => setTimespan(e.target.value)} className="w-full">
                  {MASSIVE_TIMESPANS.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-[var(--text-secondary)] mb-1">Multiplier</label>
                <input
                  type="number"
                  value={multiplier}
                  onChange={(e) => setMultiplier(parseInt(e.target.value) || 1)}
                  className="w-full"
                  min="1"
                />
              </div>
              <div>
                <label className="block text-sm text-[var(--text-secondary)] mb-1">Field</label>
                <select value={field} onChange={(e) => setField(e.target.value)} className="w-full">
                  {MASSIVE_FIELDS.map((f) => (
                    <option key={f} value={f}>{f}</option>
                  ))}
                </select>
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="block text-sm text-[var(--text-secondary)] mb-1">Dimension</label>
                <select value={dimension} onChange={(e) => setDimension(e.target.value)} className="w-full">
                  {SF1_DIMENSIONS.map((d) => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-[var(--text-secondary)] mb-1">Column</label>
                <select value={column} onChange={(e) => setColumn(e.target.value)} className="w-full">
                  {SF1_COLUMNS.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            </>
          )}
          
          <div className="lg:col-span-2">
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Description</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full"
              placeholder="Optional description"
            />
          </div>
          
          <div className="flex items-end">
            <button onClick={handleCreate} className="btn btn-primary flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Register
            </button>
          </div>
        </div>
        
        {symbol && (
          <div className="mt-3 text-sm text-[var(--text-secondary)]">
            ID: <code className="bg-[var(--bg-primary)] px-2 py-1 rounded">{generateSignalId()}</code>
            {' | '}
            Spec: <code className="bg-[var(--bg-primary)] px-2 py-1 rounded">{generateSpec()}</code>
          </div>
        )}
      </div>
      
      {/* Signals Table */}
      <div>
        <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-3">
          Registered Signals ({signals.length})
        </h3>
        
        {signals.length === 0 ? (
          <div className="text-center py-8 text-[var(--text-secondary)]">
            No signals registered. Create one above.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Source</th>
                  <th>Spec</th>
                  <th>Description</th>
                  <th>Enabled</th>
                  <th className="w-20">Actions</th>
                </tr>
              </thead>
              <tbody>
                {signals.map((signal) => (
                  <tr key={signal.id} className={!signal.enabled ? 'opacity-50' : ''}>
                    <td className="font-mono text-sm">{signal.id}</td>
                    <td className="capitalize">{signal.source}</td>
                    <td className="font-mono text-sm">{signal.spec}</td>
                    <td className="text-[var(--text-secondary)]">{signal.description}</td>
                    <td>
                      <button onClick={() => handleToggle(signal.id)}>
                        {signal.enabled ? (
                          <ToggleRight className="w-6 h-6 text-green-400" />
                        ) : (
                          <ToggleLeft className="w-6 h-6 text-gray-400" />
                        )}
                      </button>
                    </td>
                    <td>
                      <button
                        onClick={() => handleDelete(signal.id)}
                        className="text-red-400 hover:text-red-300"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
