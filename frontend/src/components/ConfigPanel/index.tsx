import { useState } from 'react';
import { JobsTab } from './JobsTab';
import { TestsTab } from './TestsTab';
import { SignalsTab } from './SignalsTab';
import { AgentsTab } from './AgentsTab';

interface ConfigPanelProps {
  onStartSimulation: () => void;
}

type TabId = 'jobs' | 'tests' | 'signals' | 'agents';

const tabs: { id: TabId; label: string }[] = [
  { id: 'jobs', label: 'Jobs' },
  { id: 'tests', label: 'Test Definitions' },
  { id: 'signals', label: 'Signals' },
  { id: 'agents', label: 'Agent Builder' },
];

export function ConfigPanel({ onStartSimulation }: ConfigPanelProps) {
  const [activeTab, setActiveTab] = useState<TabId>('jobs');
  
  return (
    <div className="p-6">
      {/* Tab Navigation */}
      <div className="flex border-b border-[var(--border-color)] mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      
      {/* Tab Content */}
      <div className="card p-6">
        {activeTab === 'jobs' && <JobsTab onStartSimulation={onStartSimulation} />}
        {activeTab === 'tests' && <TestsTab />}
        {activeTab === 'signals' && <SignalsTab />}
        {activeTab === 'agents' && <AgentsTab />}
      </div>
    </div>
  );
}
