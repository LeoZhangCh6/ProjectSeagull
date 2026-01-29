import { useState, useEffect, useCallback } from 'react';
import { Trash2, Plus, RefreshCw, Edit2, Check, X } from 'lucide-react';
import { testsApi } from '../../api/client';
import type { TestDefinition } from '../../types';

type EditingCell = {
  testName: string;
  field: keyof TestDefinition;
} | null;

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
  
  // Inline editing state
  const [editingCell, setEditingCell] = useState<EditingCell>(null);
  const [editValue, setEditValue] = useState<string>('');
  
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
  
  const handleStartEdit = (testName: string, field: keyof TestDefinition, currentValue: string | number | boolean | undefined) => {
    setEditingCell({ testName, field });
    setEditValue(currentValue?.toString() ?? '');
  };
  
  const handleCancelEdit = () => {
    setEditingCell(null);
    setEditValue('');
  };
  
  const handleConfirmEdit = async () => {
    if (!editingCell) return;
    
    const { testName, field } = editingCell;
    
    // Parse value based on field type
    let parsedValue: string | number | boolean | undefined;
    switch (field) {
      case 'trials':
      case 'trading_days':
        parsedValue = parseInt(editValue) || 1;
        break;
      case 'seed':
        parsedValue = editValue ? parseInt(editValue) : undefined;
        break;
      case 'record_curves':
        parsedValue = editValue === 'true';
        break;
      default:
        parsedValue = editValue;
    }
    
    // Validate if it's a name field
    if (field === 'name' && (!editValue || !editValue.trim())) {
      setError('Name cannot be empty');
      return;
    }
    
    // Validate date fields
    if (field === 'overall_start_date' || field === 'overall_end_date') {
      const test = tests.find(t => t.name === testName);
      if (test) {
        const startDate = new Date(field === 'overall_start_date' ? editValue : test.overall_start_date);
        const endDate = new Date(field === 'overall_end_date' ? editValue : test.overall_end_date);
        
        if (startDate >= endDate) {
          setError('Start date must be before end date');
          return;
        }
      }
    }
    
    try {
      await testsApi.update(testName, { [field]: parsedValue });
      setEditingCell(null);
      setEditValue('');
      setError(null);
      await loadTests();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to update test');
    }
  };
  
  const renderEditableCell = (
    test: TestDefinition,
    field: keyof TestDefinition,
    displayValue: string | number | boolean | undefined,
    inputType: 'text' | 'number' | 'date' = 'text'
  ) => {
    const isEditing = editingCell?.testName === test.name && editingCell?.field === field;
    
    if (isEditing) {
      return (
        <div className="flex items-center gap-1">
          <input
            type={inputType}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            className="w-full text-sm px-2 py-1"
            autoFocus
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleConfirmEdit();
              if (e.key === 'Escape') handleCancelEdit();
            }}
          />
          <button
            onClick={handleConfirmEdit}
            className="text-green-400 hover:text-green-300 p-1"
            title="Confirm"
          >
            <Check className="w-3 h-3" />
          </button>
          <button
            onClick={handleCancelEdit}
            className="text-gray-400 hover:text-gray-300 p-1"
            title="Cancel"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      );
    }
    
    return (
      <div 
        className="group flex items-center gap-1 cursor-pointer hover:bg-[var(--bg-tertiary)] rounded px-1 -mx-1"
        onClick={() => handleStartEdit(test.name, field, displayValue)}
      >
        <span>{displayValue?.toString() ?? '-'}</span>
        <Edit2 className="w-3 h-3 text-gray-500 opacity-0 group-hover:opacity-100" />
      </div>
    );
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
                  <th>Seed</th>
                  <th>Record Curves</th>
                  <th>Plot Dir</th>
                  <th className="w-20">Actions</th>
                </tr>
              </thead>
              <tbody>
                {tests.map((test) => (
                  <tr key={test.name}>
                    <td className="font-medium">
                      {renderEditableCell(test, 'name', test.name, 'text')}
                    </td>
                    <td>
                      {renderEditableCell(test, 'trials', test.trials, 'number')}
                    </td>
                    <td>
                      {renderEditableCell(test, 'overall_start_date', test.overall_start_date, 'date')}
                    </td>
                    <td>
                      {renderEditableCell(test, 'overall_end_date', test.overall_end_date, 'date')}
                    </td>
                    <td>
                      {renderEditableCell(test, 'trading_days', test.trading_days, 'number')}
                    </td>
                    <td>
                      {renderEditableCell(test, 'seed', test.seed, 'number')}
                    </td>
                    <td>
                      <button
                        onClick={async () => {
                          try {
                            await testsApi.update(test.name, { record_curves: !test.record_curves });
                            await loadTests();
                          } catch (e) {
                            setError(e instanceof Error ? e.message : 'Failed to update');
                          }
                        }}
                        className={`px-2 py-1 rounded text-xs ${test.record_curves ? 'bg-green-600 text-white' : 'bg-gray-600 text-gray-300'}`}
                      >
                        {test.record_curves ? 'Yes' : 'No'}
                      </button>
                    </td>
                    <td>
                      {renderEditableCell(test, 'plot_dir', test.plot_dir, 'text')}
                    </td>
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
