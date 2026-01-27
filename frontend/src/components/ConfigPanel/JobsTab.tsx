import { useState, useEffect, useCallback } from 'react';
import { Play, Trash2, Plus, RefreshCw } from 'lucide-react';
import { jobsApi, simulationApi } from '../../api/client';
import { useSimulationStore } from '../../stores/simulationStore';
import type { Job } from '../../types';

interface JobsTabProps {
  onStartSimulation: () => void;
}

export function JobsTab({ onStartSimulation }: JobsTabProps) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [availableTests, setAvailableTests] = useState<string[]>([]);
  const [availableAgents, setAvailableAgents] = useState<string[]>([]);
  const [selectedTest, setSelectedTest] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  
  const { setSessionId, reset } = useSimulationStore();
  
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [jobsData, testsData, agentsData] = await Promise.all([
        jobsApi.list(),
        jobsApi.availableTests(),
        jobsApi.availableAgents(),
      ]);
      setJobs(jobsData);
      setAvailableTests(testsData);
      setAvailableAgents(agentsData);
      
      if (testsData.length > 0 && !selectedTest) setSelectedTest(testsData[0]);
      if (agentsData.length > 0 && !selectedAgent) setSelectedAgent(agentsData[0]);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [selectedTest, selectedAgent]);
  
  useEffect(() => {
    loadData();
  }, []);
  
  const handleCreateJob = async () => {
    if (!selectedTest || !selectedAgent) return;
    
    try {
      await jobsApi.create({ test_name: selectedTest, agent_name: selectedAgent });
      await loadData();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create job');
    }
  };
  
  const handleDeleteJob = async (testName: string, agentName: string) => {
    try {
      await jobsApi.delete(testName, agentName);
      await loadData();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete job');
    }
  };
  
  const handleDeleteAll = async () => {
    if (!confirm('Delete all jobs?')) return;
    try {
      await jobsApi.deleteAll();
      await loadData();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete jobs');
    }
  };
  
  const handleStartSimulation = async () => {
    if (jobs.length === 0) {
      setError('No jobs to run');
      return;
    }
    
    setStarting(true);
    setError(null);
    reset();
    
    try {
      // Get session ID from REST API
      const response = await simulationApi.start();
      console.log('[JobsTab] Got session ID:', response.session_id);
      
      // Set session ID - the SimulationDashboard will handle WebSocket connection
      setSessionId(response.session_id);
      
      // Navigate to simulation view
      onStartSimulation();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to start simulation');
      setStarting(false);
    }
  };
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Job Management</h2>
        <div className="flex gap-2">
          <button onClick={loadData} className="btn btn-secondary" disabled={loading}>
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button 
            onClick={handleStartSimulation} 
            className="btn btn-primary flex items-center gap-2"
            disabled={jobs.length === 0 || starting}
          >
            {starting ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Starting...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Start Simulation
              </>
            )}
          </button>
        </div>
      </div>
      
      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-2 rounded">
          {error}
        </div>
      )}
      
      {/* Create Job Form */}
      <div className="card p-4 bg-[var(--bg-tertiary)]">
        <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-3">Create Job</h3>
        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Test</label>
            <select 
              value={selectedTest} 
              onChange={(e) => setSelectedTest(e.target.value)}
              className="w-full"
            >
              {availableTests.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Agent</label>
            <select 
              value={selectedAgent} 
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="w-full"
            >
              {availableAgents.map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>
          <button onClick={handleCreateJob} className="btn btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Add Job
          </button>
        </div>
      </div>
      
      {/* Jobs Table */}
      <div>
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-sm font-medium text-[var(--text-secondary)]">
            Jobs ({jobs.length})
          </h3>
          {jobs.length > 0 && (
            <button onClick={handleDeleteAll} className="btn btn-danger text-xs">
              Delete All
            </button>
          )}
        </div>
        
        {jobs.length === 0 ? (
          <div className="text-center py-8 text-[var(--text-secondary)]">
            No jobs configured. Create a job to run simulations.
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Test Name</th>
                <th>Agent Name</th>
                <th className="w-20">Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={`${job.test_name}-${job.agent_name}`}>
                  <td>{job.test_name}</td>
                  <td>{job.agent_name}</td>
                  <td>
                    <button
                      onClick={() => handleDeleteJob(job.test_name, job.agent_name)}
                      className="text-red-400 hover:text-red-300"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
