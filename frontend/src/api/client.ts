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
