import { useState, useEffect, useCallback, useRef } from 'react';
import { Trash2, Copy, RefreshCw, ToggleLeft, ToggleRight, Eye, Upload, Edit2, Check, X, Workflow, Plus } from 'lucide-react';
import { agentsApi, visualDesignerApi } from '../../api/client';
import type { Agent, VisualDesign, DesignTemplate } from '../../types';
import { VisualDesigner } from '../VisualDesigner';

export function AgentsTab() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewingCode, setViewingCode] = useState<string | null>(null);
  
  // Clone form state
  const [sourceAgent, setSourceAgent] = useState('');
  const [newAgentName, setNewAgentName] = useState('');
  
  // Upload form state
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadAgentName, setUploadAgentName] = useState('');
  const [uploadDescription, setUploadDescription] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  
  // Rename state
  const [editingName, setEditingName] = useState<string | null>(null);
  const [editNameValue, setEditNameValue] = useState('');
  
  // Visual Designer state
  const [showDesigner, setShowDesigner] = useState(false);
  const [visualDesigns, setVisualDesigns] = useState<VisualDesign[]>([]);
  const [templates, setTemplates] = useState<DesignTemplate[]>([]);
  const [editingDesign, setEditingDesign] = useState<VisualDesign | undefined>(undefined);
  
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
    loadVisualDesigns();
    loadTemplates();
  }, []);
  
  const loadVisualDesigns = async () => {
    try {
      const data = await visualDesignerApi.list();
      setVisualDesigns(data);
    } catch (e) {
      console.error('Failed to load visual designs:', e);
    }
  };
  
  const loadTemplates = async () => {
    try {
      const data = await visualDesignerApi.listTemplates();
      setTemplates(data);
    } catch (e) {
      console.error('Failed to load templates:', e);
    }
  };
  
  const handleOpenDesigner = (design?: VisualDesign) => {
    setEditingDesign(design);
    setShowDesigner(true);
  };
  
  const handleCloseDesigner = () => {
    setShowDesigner(false);
    setEditingDesign(undefined);
    loadVisualDesigns();
    loadAgents();
  };
  
  const handleDeleteDesign = async (id: number, name: string) => {
    if (!confirm(`Delete design "${name}"?`)) return;
    try {
      await visualDesignerApi.delete(id);
      await loadVisualDesigns();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete design');
    }
  };
  
  const handleCreateFromTemplate = async (templateName: string) => {
    const designName = prompt('Enter a name for the new design:');
    if (!designName) return;
    
    try {
      const design = await visualDesignerApi.createFromTemplate(templateName, designName);
      setEditingDesign(design);
      setShowDesigner(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create from template');
    }
  };
  
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
  
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      // Auto-fill agent name from filename if not already set
      if (!uploadAgentName) {
        setUploadAgentName(file.name.replace('.py', ''));
      }
    }
  };
  
  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a Python file to upload');
      return;
    }
    
    try {
      await agentsApi.upload(selectedFile, uploadAgentName || undefined, uploadDescription || undefined);
      setSelectedFile(null);
      setUploadAgentName('');
      setUploadDescription('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      await loadAgents();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to upload agent');
    }
  };
  
  const handleStartRename = (name: string) => {
    setEditingName(name);
    setEditNameValue(name);
  };
  
  const handleCancelRename = () => {
    setEditingName(null);
    setEditNameValue('');
  };
  
  const handleConfirmRename = async () => {
    if (!editingName || !editNameValue.trim()) {
      setError('Agent name cannot be empty');
      return;
    }
    
    if (editNameValue.trim() === editingName) {
      handleCancelRename();
      return;
    }
    
    try {
      await agentsApi.rename(editingName, editNameValue.trim());
      setEditingName(null);
      setEditNameValue('');
      await loadAgents();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to rename agent');
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
      
      {/* Visual Agent Designer Section */}
      <div className="card p-4 bg-gradient-to-r from-purple-900/30 to-blue-900/30 border-purple-500/50">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Workflow className="w-5 h-5 text-purple-400" />
            <h3 className="text-sm font-medium">Visual Agent Designer</h3>
          </div>
          <button 
            onClick={() => handleOpenDesigner()}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New Design
          </button>
        </div>
        
        <p className="text-xs text-[var(--text-secondary)] mb-4">
          Design agents visually with a node-based interface. Connect signals, operations, and ML layers to create trading strategies without writing code.
        </p>
        
        {/* Templates */}
        {templates.length > 0 && (
          <div className="mb-4">
            <div className="text-xs text-[var(--text-secondary)] mb-2">Start from a template:</div>
            <div className="flex flex-wrap gap-2">
              {templates.map(t => (
                <button
                  key={t.name}
                  onClick={() => handleCreateFromTemplate(t.name)}
                  className="px-3 py-1.5 text-xs rounded bg-[var(--bg-tertiary)] hover:bg-[var(--bg-secondary)] border border-[var(--border-color)] transition-colors"
                  title={t.description}
                >
                  {t.title}
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* Saved Designs */}
        {visualDesigns.length > 0 && (
          <div>
            <div className="text-xs text-[var(--text-secondary)] mb-2">Saved designs ({visualDesigns.length}):</div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {visualDesigns.map(d => (
                <div
                  key={d.id}
                  className="p-2 rounded bg-[var(--bg-tertiary)] border border-[var(--border-color)] hover:border-purple-500/50 transition-colors group"
                >
                  <div className="flex items-center justify-between">
                    <button
                      onClick={() => handleOpenDesigner(d)}
                      className="text-sm font-medium hover:text-purple-400 truncate flex-1 text-left"
                    >
                      {d.name}
                    </button>
                    <button
                      onClick={() => handleDeleteDesign(d.id, d.name)}
                      className="p-1 text-red-400 hover:text-red-300 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                  <div className="text-xs text-[var(--text-secondary)] truncate">
                    {d.symbol} • {d.primary_timespan}×{d.primary_multiplier}
                    {d.agent_name && <span className="ml-1 text-green-400">• Deployed</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      
      {/* Upload Agent Form */}
      <div className="card p-4 bg-[var(--bg-tertiary)]">
        <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-3">Upload Agent from File</h3>
        <div className="flex gap-4 items-end flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Python File</label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".py"
              onChange={handleFileSelect}
              className="w-full"
            />
          </div>
          <div className="flex-1 min-w-[150px]">
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Agent Name (optional)</label>
            <input
              type="text"
              value={uploadAgentName}
              onChange={(e) => setUploadAgentName(e.target.value)}
              className="w-full"
              placeholder="my_agent"
            />
          </div>
          <div className="flex-1 min-w-[150px]">
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Description (optional)</label>
            <input
              type="text"
              value={uploadDescription}
              onChange={(e) => setUploadDescription(e.target.value)}
              className="w-full"
              placeholder="Agent description"
            />
          </div>
          <button 
            onClick={handleUpload} 
            className="btn btn-primary flex items-center gap-2"
            disabled={!selectedFile}
          >
            <Upload className="w-4 h-4" />
            Upload
          </button>
        </div>
        {selectedFile && (
          <p className="mt-2 text-sm text-[var(--text-secondary)]">
            Selected: {selectedFile.name}
          </p>
        )}
      </div>
      
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
                    <td className="font-medium">
                      {editingName === agent.name ? (
                        <div className="flex items-center gap-2">
                          <input
                            type="text"
                            value={editNameValue}
                            onChange={(e) => setEditNameValue(e.target.value)}
                            className="w-full text-sm px-2 py-1"
                            autoFocus
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleConfirmRename();
                              if (e.key === 'Escape') handleCancelRename();
                            }}
                          />
                          <button
                            onClick={handleConfirmRename}
                            className="text-green-400 hover:text-green-300 p-1"
                            title="Confirm"
                          >
                            <Check className="w-4 h-4" />
                          </button>
                          <button
                            onClick={handleCancelRename}
                            className="text-gray-400 hover:text-gray-300 p-1"
                            title="Cancel"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ) : (
                        agent.name
                      )}
                    </td>
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
                        <button
                          onClick={() => handleStartRename(agent.name)}
                          className="text-yellow-400 hover:text-yellow-300 p-1"
                          title="Rename"
                          disabled={editingName !== null}
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
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
      
      {/* Visual Designer Modal */}
      <VisualDesigner
        isOpen={showDesigner}
        onClose={handleCloseDesigner}
        initialDesign={editingDesign}
      />
    </div>
  );
}
