import React from 'react';
import type { HistoryRunSummary } from '../../types/mfrecon.types';
import { Eye, Calendar, FileSpreadsheet } from 'lucide-react';

interface RunHistoryCardProps {
  run: HistoryRunSummary;
  onViewRun: (runId: string) => void;
}

export const RunHistoryCard: React.FC<RunHistoryCardProps> = ({ run, onViewRun }) => {
  const getStatusColor = (status: string) => {
    if (status === 'success') return '#10b981';
    if (status === 'partial') return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="card flex flex-col gap-4" style={{ padding: '16px', cursor: 'pointer' }} onClick={() => onViewRun(run.run_id)}>
      <div className="flex justify-between items-center w-full">
        <span className="font-bold text-sm" style={{ color: 'hsl(var(--text-primary))', fontFamily: 'monospace' }}>{run.run_id}</span>
        <span 
          className="badge" 
          style={{ 
            backgroundColor: `${getStatusColor(run.status)}15`, 
            color: getStatusColor(run.status),
            border: `1px solid ${getStatusColor(run.status)}30`
          }}
        >
          {run.status}
        </span>
      </div>

      <div className="flex flex-col gap-1 text-xs text-muted">
        <div className="flex items-center gap-2">
          <Calendar size={12} />
          <span>{new Date(run.timestamp).toLocaleDateString()}</span>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <FileSpreadsheet size={12} style={{ color: '#10b981' }} />
          <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '200px' }}>
            {run.crm_filename}
          </span>
        </div>
      </div>

      <div className="flex justify-between items-center w-full mt-2" style={{ borderTop: '1px solid hsl(var(--border-color))', paddingTop: '10px' }}>
        <div className="flex flex-col">
          <span style={{ fontSize: '0.7rem', color: 'hsl(var(--text-muted))' }}>Match Coverage</span>
          <span className="font-bold text-sm" style={{ color: run.match_rate_percent >= 90 ? '#10b981' : '#f59e0b' }}>
            {run.match_rate_percent.toFixed(1)}%
          </span>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onViewRun(run.run_id);
          }}
          className="btn-secondary"
          style={{ padding: '6px 12px', fontSize: '0.75rem', borderRadius: '4px', border: 'none' }}
        >
          <Eye size={10} className="mr-1" />
          <span>Inspect</span>
        </button>
      </div>
    </div>
  );
};
