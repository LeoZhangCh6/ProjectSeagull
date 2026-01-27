import { useState, useEffect, useCallback } from 'react';
import { Trash2, Plus, RefreshCw } from 'lucide-react';
import { testsApi } from '../../api/client';
import type { TestDefinition } from '../../types';

export function TestsTab() {
  const [tests, setTests] = useState<TestDefinition[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form state
  const [form, setForm] = useState<Partial<TestDefinition>>({
    name: '',
    trials: 1,
    overall_start_date: '2023-01-01',
    overall_end_date: '2023-12-31',
    trading_days: 14,
    record_curves: false,
    plot_dir: '',
  });
  
  const loadTests = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await testsApi.list();
      setTests(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load tests');
    } finally {
      setLoading(false);
    }
  }, []);
  
  useEffect(() => {
    loadTests();
  }, [loadTests]);
  
  const handleCreate = async () => {
    if (!form.name || !form.overall_start_date || !form.overall_end_date) {
      setError('Name and dates are required');
      return;
    }
    
    // Validate date range
    const startDate = new Date(form.overall_start_date);
    const endDate = new Date(form.overall_end_date);
    
    if (startDate >= endDate) {
      setError('Start date must be before end date');
      return;
    }
    
    const daysDiff = Math.floor((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
    if (daysDiff < 7) {
      setError(`Date range too short (${daysDiff} days). Need at least 7 calendar days to ensure trading days.`);
      return;
    }
    
    try {
      await testsApi.create(form as TestDefinition);
      setForm({
        name: '',
        trials: 1,
        overall_start_date: '2023-01-01',
        overall_end_date: '2023-12-31',
        trading_days: 14,
        record_curves: false,
        plot_dir: '',
      });
      await loadTests();
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create test');
    }
  };
  
  const handleDelete = async (name: string) => {
    if (!confirm(`Delete test "${name}"?`)) return;
    try {
      await testsApi.delete(name);
      await loadTests();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete test');
    }
  };
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Test Definitions</h2>
        <button onClick={loadTests} className="btn btn-secondary" disabled={loading}>
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>
      
      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-2 rounded">
          {error}
        </div>
      )}
      
      {/* Create Test Form */}
      <div className="card p-4 bg-[var(--bg-tertiary)]">
        <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-3">Create Test Definition</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Name *</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full"
              placeholder="my_test"
            />
          </div>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Trials</label>
            <input
              type="number"
              value={form.trials}
              onChange={(e) => setForm({ ...form, trials: parseInt(e.target.value) || 1 })}
              className="w-full"
              min="1"
            />
          </div>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Start Date *</label>
            <input
              type="date"
              value={form.overall_start_date}
              onChange={(e) => setForm({ ...form, overall_start_date: e.target.value })}
              className="w-full"
            />
          </div>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">End Date *</label>
            <input
              type="date"
              value={form.overall_end_date}
              onChange={(e) => setForm({ ...form, overall_end_date: e.target.value })}
              className="w-full"
            />
          </div>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Trading Days</label>
            <input
              type="number"
              value={form.trading_days}
              onChange={(e) => setForm({ ...form, trading_days: parseInt(e.target.value) || 14 })}
              className="w-full"
              min="1"
            />
          </div>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Seed (optional)</label>
            <input
              type="number"
              value={form.seed ?? ''}
              onChange={(e) => setForm({ ...form, seed: e.target.value ? parseInt(e.target.value) : undefined })}
              className="w-full"
              placeholder="42"
            />
          </div>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Plot Directory</label>
            <input
              type="text"
              value={form.plot_dir ?? ''}
              onChange={(e) => setForm({ ...form, plot_dir: e.target.value || undefined })}
              className="w-full"
              placeholder="C:\output"
            />
          </div>
          <div className="flex items-end gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={form.record_curves}
                onChange={(e) => setForm({ ...form, record_curves: e.target.checked })}
                className="w-4 h-4"
              />
              <span className="text-sm">Record Curves</span>
            </label>
            <button onClick={handleCreate} className="btn btn-primary flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Create
            </button>
          </div>
        </div>
      </div>
      
      {/* Tests Table */}
      <div>
        <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-3">
          Existing Tests ({tests.length})
        </h3>
        
        {tests.length === 0 ? (
          <div className="text-center py-8 text-[var(--text-secondary)]">
            No test definitions. Create one above.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Trials</th>
                  <th>Start Date</th>
                  <th>End Date</th>
                  <th>Trading Days</th>
                  <th className="w-20">Actions</th>
                </tr>
              </thead>
              <tbody>
                {tests.map((test) => (
                  <tr key={test.name}>
                    <td className="font-medium">{test.name}</td>
                    <td>{test.trials}</td>
                    <td>{test.overall_start_date}</td>
                    <td>{test.overall_end_date}</td>
                    <td>{test.trading_days}</td>
                    <td>
                      <button
                        onClick={() => handleDelete(test.name)}
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
