import { useState } from 'react';
import { ConfigPanel } from './components/ConfigPanel';
import { SimulationDashboard } from './components/Dashboard/SimulationDashboard';
import { useSimulationStore } from './stores/simulationStore';

type View = 'config' | 'simulation';

function App() {
  const [view, setView] = useState<View>('config');
  const simulationStatus = useSimulationStore((s) => s.status);
  
  // Auto-switch to simulation view when running
  const effectiveView = simulationStatus === 'running' || simulationStatus === 'completed' 
    ? 'simulation' 
    : view;
  
  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Header */}
      <header className="border-b border-[var(--border-color)] bg-[var(--bg-secondary)]">
        <div className="max-w-[1920px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold text-white">ProjectSeagull</h1>
            <span className="text-sm text-[var(--text-secondary)]">Simulation Dashboard</span>
          </div>
          
          <nav className="flex items-center gap-2">
            <button
              onClick={() => setView('config')}
              className={`tab-button ${effectiveView === 'config' ? 'active' : ''}`}
            >
              Configuration
            </button>
            <button
              onClick={() => setView('simulation')}
              className={`tab-button ${effectiveView === 'simulation' ? 'active' : ''}`}
              disabled={simulationStatus === 'idle'}
            >
              Simulation
              {simulationStatus === 'running' && (
                <span className="ml-2 inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              )}
            </button>
          </nav>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="max-w-[1920px] mx-auto">
        {effectiveView === 'config' ? (
          <ConfigPanel onStartSimulation={() => setView('simulation')} />
        ) : (
          <SimulationDashboard onBack={() => setView('config')} />
        )}
      </main>
    </div>
  );
}

export default App;
