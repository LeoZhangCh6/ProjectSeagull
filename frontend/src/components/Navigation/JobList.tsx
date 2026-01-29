import { CheckCircle, Clock, AlertCircle, Loader2 } from 'lucide-react';
import type { JobStatus } from '../../types';

interface JobListProps {
  jobs: JobStatus[];
  activeIndex: number;
  onSelect: (index: number) => void;
}

export function JobList({ jobs, activeIndex, onSelect }: JobListProps) {
  if (jobs.length === 0) {
    return (
      <div className="p-4 text-center text-[var(--text-secondary)]">
        No jobs running
      </div>
    );
  }
  
  return (
    <div className="divide-y divide-[var(--border-color)]">
      {jobs.map((job, index) => (
        <button
          key={job.job_id}
          onClick={() => onSelect(index)}
          className={`w-full p-4 text-left hover:bg-[var(--bg-tertiary)] transition-colors ${
            index === activeIndex ? 'bg-[var(--bg-tertiary)] border-l-2 border-l-[var(--accent-blue)]' : ''
          }`}
        >
          <div className="flex items-center gap-3">
            <StatusIcon status={job.status} />
            <div className="flex-1 min-w-0">
              <div className="font-medium truncate">{job.test_name}</div>
              <div className="text-sm text-[var(--text-secondary)] truncate">
                {job.agent_name}
              </div>
            </div>
          </div>
          
          {/* Progress Bar - show for both pending and running jobs */}
          {(job.status === 'running' || job.status === 'pending') && (
            <div className="mt-2">
              <div className="text-xs text-[var(--text-secondary)] mb-1">
                {job.progress_message || (job.status === 'pending' ? 'Queued...' : 'Starting...')}
              </div>
              <div className="w-full bg-gray-700 rounded-full h-1.5">
                <div 
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    job.status === 'pending' ? 'bg-yellow-500' : 'bg-blue-500'
                  }`}
                  style={{ width: `${job.progress_percent ?? 0}%` }}
                />
              </div>
            </div>
          )}
          
          {job.bars.length > 0 && (
            <div className="mt-2 flex justify-between text-xs text-[var(--text-secondary)]">
              <span>{job.bars.length} bars</span>
              <span>{job.trades.length} trades</span>
            </div>
          )}
          
          {job.final_result && (
            <div className="mt-2 text-sm">
              {job.final_result.error ? (
                <span className="text-red-400">Error</span>
              ) : (
                <span className={job.final_result.final_equity && job.final_result.final_equity > 100000 
                  ? 'text-green-400' 
                  : 'text-red-400'
                }>
                  ${job.final_result.final_equity?.toLocaleString(undefined, { 
                    minimumFractionDigits: 2, 
                    maximumFractionDigits: 2 
                  })}
                </span>
              )}
            </div>
          )}
        </button>
      ))}
    </div>
  );
}

function StatusIcon({ status }: { status: JobStatus['status'] }) {
  switch (status) {
    case 'pending':
      return <Clock className="w-5 h-5 text-yellow-400 animate-pulse" />;
    case 'running':
      return <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />;
    case 'completed':
      return <CheckCircle className="w-5 h-5 text-green-400" />;
    case 'error':
      return <AlertCircle className="w-5 h-5 text-red-400" />;
    default:
      return <Clock className="w-5 h-5 text-gray-400" />;
  }
}
