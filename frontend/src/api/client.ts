// API Client for ProjectSeagull backend

const API_BASE = '/api';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'API Error');
  }
  return response.json();
}

// Signals API
export const signalsApi = {
  list: () => 
    fetch(`${API_BASE}/signals`).then(handleResponse<import('../types').Signal[]>),
  
  get: (id: string) => 
    fetch(`${API_BASE}/signals/${id}`).then(handleResponse<import('../types').Signal>),
  
  create: (signal: import('../types').Signal) =>
    fetch(`${API_BASE}/signals`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(signal),
    }).then(handleResponse<import('../types').Signal>),
  
  delete: (id: string) =>
    fetch(`${API_BASE}/signals/${id}`, { method: 'DELETE' }).then(handleResponse),
  
  toggle: (id: string) =>
    fetch(`${API_BASE}/signals/${id}/toggle`, { method: 'PATCH' }).then(handleResponse),
};

// Tests API
export const testsApi = {
  list: () =>
    fetch(`${API_BASE}/tests`).then(handleResponse<import('../types').TestDefinition[]>),
  
  get: (name: string) =>
    fetch(`${API_BASE}/tests/${name}`).then(handleResponse<import('../types').TestDefinition>),
  
  create: (test: import('../types').TestDefinition) =>
    fetch(`${API_BASE}/tests`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(test),
    }).then(handleResponse<import('../types').TestDefinition>),
  
  delete: (name: string) =>
    fetch(`${API_BASE}/tests/${name}`, { method: 'DELETE' }).then(handleResponse),
  
  update: (name: string, updates: Partial<import('../types').TestDefinition>) =>
    fetch(`${API_BASE}/tests/${name}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    }).then(handleResponse<import('../types').TestDefinition>),
};

// Jobs API
export const jobsApi = {
  list: () =>
    fetch(`${API_BASE}/jobs`).then(handleResponse<import('../types').Job[]>),
  
  availableTests: () =>
    fetch(`${API_BASE}/jobs/available-tests`).then(handleResponse<string[]>),
  
  availableAgents: () =>
    fetch(`${API_BASE}/jobs/available-agents`).then(handleResponse<string[]>),
  
  create: (job: import('../types').Job) =>
    fetch(`${API_BASE}/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(job),
    }).then(handleResponse<import('../types').Job>),
  
  delete: (testName: string, agentName: string) =>
    fetch(`${API_BASE}/jobs/${testName}/${agentName}`, { method: 'DELETE' }).then(handleResponse),
  
  deleteAll: () =>
    fetch(`${API_BASE}/jobs`, { method: 'DELETE' }).then(handleResponse),
};

// Agents API
export const agentsApi = {
  list: () =>
    fetch(`${API_BASE}/agents`).then(handleResponse<import('../types').Agent[]>),
  
  get: (name: string) =>
    fetch(`${API_BASE}/agents/${name}`).then(handleResponse<import('../types').Agent>),
  
  create: (agent: import('../types').Agent) =>
    fetch(`${API_BASE}/agents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(agent),
    }).then(handleResponse<import('../types').Agent>),
  
  clone: (sourceName: string, newName: string) =>
    fetch(`${API_BASE}/agents/clone`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_name: sourceName, new_name: newName }),
    }).then(handleResponse<import('../types').Agent>),
  
  delete: (name: string) =>
    fetch(`${API_BASE}/agents/${name}`, { method: 'DELETE' }).then(handleResponse),
  
  toggle: (name: string) =>
    fetch(`${API_BASE}/agents/${name}/toggle`, { method: 'PATCH' }).then(handleResponse),
  
  rename: (name: string, newName: string) =>
    fetch(`${API_BASE}/agents/${name}/rename`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_name: newName }),
    }).then(handleResponse<import('../types').Agent>),
  
  upload: (file: File, agentName?: string, description?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (agentName) formData.append('agent_name', agentName);
    if (description) formData.append('description', description);
    return fetch(`${API_BASE}/agents/upload`, {
      method: 'POST',
      body: formData,
    }).then(handleResponse<import('../types').Agent>);
  },
};

// Simulation API
export const simulationApi = {
  start: (jobIds?: string[], testNames?: string[]) =>
    fetch(`${API_BASE}/simulation/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_ids: jobIds, test_names: testNames }),
    }).then(handleResponse<{ session_id: string; status: string }>),
  
  status: (sessionId: string) =>
    fetch(`${API_BASE}/simulation/status/${sessionId}`).then(handleResponse),
  
  stop: (sessionId: string) =>
    fetch(`${API_BASE}/simulation/stop/${sessionId}`, { method: 'POST' }).then(handleResponse),
};

// Visual Designer API
export const visualDesignerApi = {
  // CRUD for designs
  list: () =>
    fetch(`${API_BASE}/visual-designer`).then(handleResponse<import('../types').VisualDesign[]>),
  
  get: (id: number) =>
    fetch(`${API_BASE}/visual-designer/${id}`).then(handleResponse<import('../types').VisualDesign>),
  
  create: (design: import('../types').VisualDesignCreate) =>
    fetch(`${API_BASE}/visual-designer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(design),
    }).then(handleResponse<import('../types').VisualDesign>),
  
  update: (id: number, updates: Partial<import('../types').VisualDesignCreate>) =>
    fetch(`${API_BASE}/visual-designer/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    }).then(handleResponse<import('../types').VisualDesign>),
  
  delete: (id: number) =>
    fetch(`${API_BASE}/visual-designer/${id}`, { method: 'DELETE' }).then(handleResponse),
  
  // Code generation
  generateCode: (graph: import('../types').VisualDesignGraph, symbol: string, timespan: string, multiplier: number) =>
    fetch(`${API_BASE}/visual-designer/generate-code`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ graph_json: graph, symbol, primary_timespan: timespan, primary_multiplier: multiplier }),
    }).then(handleResponse<import('../types').CodeGenerationResult>),
  
  generateCodeForDesign: (id: number) =>
    fetch(`${API_BASE}/visual-designer/${id}/generate`, {
      method: 'POST',
    }).then(handleResponse<import('../types').CodeGenerationResult>),
  
  // Validation
  validate: (graph: import('../types').VisualDesignGraph) =>
    fetch(`${API_BASE}/visual-designer/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ graph_json: graph, symbol: 'AAPL', primary_timespan: 'day', primary_multiplier: 1 }),
    }).then(handleResponse<import('../types').ValidationResult>),
  
  // Deploy as agent
  deploy: (id: number, agentName: string, description?: string) =>
    fetch(`${API_BASE}/visual-designer/${id}/deploy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent_name: agentName, description }),
    }).then(handleResponse<import('../types').VisualDesign>),
  
  // Signal preview for sparklines
  getSignalPreview: (signalId: string, numPoints: number = 20) =>
    fetch(`${API_BASE}/visual-designer/signal-preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ signal_id: signalId, num_points: numPoints }),
    }).then(handleResponse<import('../types').SignalPreview>),
  
  // Templates
  listTemplates: () =>
    fetch(`${API_BASE}/visual-designer/templates/list`).then(handleResponse<import('../types').DesignTemplate[]>),
  
  createFromTemplate: (templateName: string, designName: string) =>
    fetch(`${API_BASE}/visual-designer/templates/${templateName}?design_name=${encodeURIComponent(designName)}`, {
      method: 'POST',
    }).then(handleResponse<import('../types').VisualDesign>),
};
