import { useState, useEffect, useCallback } from 'react';
import { Trash2, Copy, RefreshCw, ToggleLeft, ToggleRight, Eye } from 'lucide-react';
import { agentsApi } from '../../api/client';
import type { Agent } from '../../types';

export function AgentsTab() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewingCode, setViewingCode] = useState<string | null>(null);
  
  // Clone form state
  const [sourceAgent, setSourceAgent] = useState('');
  const [newAgentName, setNewAgentName] = useState('');
  
  const loadAgents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await agentsApi.list();
      setAgents(data);
      if (data.length > 0 && !sourceAgent) {
        setSourceAgent(data[0].name);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load agents');
    } finally {
      setLoading(false);
    }
  }, [sourceAgent]);
  
  useEffect(() => {
    loadAgents();
  }, []);
  
  const handleClone = async () => {
    if (!sourceAgent || !newAgentName) {
      setError('Source agent and new name are required');
      return;
    }
    
    try {
      await agentsApi.clone(sourceAgent, newAgentName);
      setNewAgentName('');
      await loadAgents();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to clone agent');
    }
  };
  
  const handleDelete = async (name: string) => {
    if (!confirm(`Delete agent "${name}"?`)) return;
    try {
      await agentsApi.delete(name);
      await loadAgents();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete agent');
    }
  };
  
  const handleToggle = async (name: string) => {
    try {
      await agentsApi.toggle(name);
      await loadAgents();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to toggle agent');
    }
  };
  
  const selectedAgentCode = agents.find(a => a.name === viewingCode)?.code;
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Agent Builder</h2>
        <button onClick={loadAgents} className="btn btn-secondary" disabled={loading}>
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>
      
      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-2 rounded">
          {error}
        </div>
      )}
      
      {/* Clone Agent Form */}
      <div className="card p-4 bg-[var(--bg-tertiary)]">
        <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-3">Clone Agent</h3>
        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Source Agent</label>
            <select 
              value={sourceAgent} 
              onChange={(e) => setSourceAgent(e.target.value)}
              className="w-full"
            >
              {agents.map((a) => (
                <option key={a.name} value={a.name}>{a.name}</option>
              ))}
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-sm text-[var(--text-secondary)] mb-1">New Agent Name</label>
            <input
              type="text"
              value={newAgentName}
              onChange={(e) => setNewAgentName(e.target.value)}
              className="w-full"
              placeholder="my_new_agent"
            />
          </div>
          <button onClick={handleClone} className="btn btn-primary flex items-center gap-2">
            <Copy className="w-4 h-4" />
            Clone
          </button>
        </div>
      </div>
      
      {/* Agents Table */}
      <div>
        <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-3">
          Registered Agents ({agents.length})
        </h3>
        
        {agents.length === 0 ? (
          <div className="text-center py-8 text-[var(--text-secondary)]">
            No agents registered. Run init_db.py to auto-register agents from Agents/instances/.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Description</th>
                  <th>Has Code</th>
                  <th>Enabled</th>
                  <th className="w-24">Actions</th>
                </tr>
              </thead>
              <tbody>
                {agents.map((agent) => (
                  <tr key={agent.name} className={!agent.enabled ? 'opacity-50' : ''}>
                    <td className="font-medium">{agent.name}</td>
                    <td className="text-[var(--text-secondary)]">{agent.description}</td>
                    <td>
                      {agent.code ? (
                        <span className="text-green-400">Yes</span>
                      ) : (
                        <span className="text-yellow-400">File only</span>
                      )}
                    </td>
                    <td>
                      <button onClick={() => handleToggle(agent.name)}>
                        {agent.enabled ? (
                          <ToggleRight className="w-6 h-6 text-green-400" />
                        ) : (
                          <ToggleLeft className="w-6 h-6 text-gray-400" />
                        )}
                      </button>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        {agent.code && (
                          <button
                            onClick={() => setViewingCode(viewingCode === agent.name ? null : agent.name)}
                            className="text-blue-400 hover:text-blue-300 p-1"
                            title="View code"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        )}
                        {!agent.code && <span className="w-6" />}
                        <button
                          onClick={() => handleDelete(agent.name)}
                          className="text-red-400 hover:text-red-300 p-1"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      
      {/* Code Viewer */}
      {viewingCode && selectedAgentCode && (
        <div className="card p-4">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-sm font-medium">Code: {viewingCode}</h3>
            <button 
              onClick={() => setViewingCode(null)}
              className="text-[var(--text-secondary)] hover:text-white"
            >
              Close
            </button>
          </div>
          <pre className="bg-[var(--bg-primary)] p-4 rounded overflow-auto max-h-96 text-sm">
            <code>{selectedAgentCode}</code>
          </pre>
        </div>
      )}
    </div>
  );
}
