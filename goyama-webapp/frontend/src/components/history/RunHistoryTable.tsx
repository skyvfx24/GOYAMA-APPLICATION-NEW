import React from 'react';
import type { HistoryRunSummary } from '../../types/mfrecon.types';
import { Eye, Calendar, FileSpreadsheet } from 'lucide-react';

interface RunHistoryTableProps {
  runs: HistoryRunSummary[];
  onViewRun: (runId: string) => void;
}

export const RunHistoryTable: React.FC<RunHistoryTableProps> = ({ runs, onViewRun }) => {
  if (runs.length === 0) {
    return (
      <div className="card text-center" style={{ padding: '48px', color: 'hsl(var(--text-secondary))' }}>
        <p className="font-medium">No previous runs found.</p>
        <p className="text-sm text-muted mt-2">Upload files and run reconciliation to generate history records.</p>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    if (status === 'success') return '#10b981'; // emerald
    if (status === 'partial') return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th>Run ID</th>
            <th>Timestamp</th>
            <th>CRM File</th>
            <th>Report Count</th>
            <th>Match Rate</th>
            <th>Status</th>
            <th style={{ textAlign: 'right' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.run_id} style={{ cursor: 'pointer' }} onClick={() => onViewRun(run.run_id)}>
              <td className="font-medium" style={{ color: 'hsl(var(--text-primary))', fontFamily: 'monospace' }}>
                {run.run_id}
              </td>
              <td>
                <div className="flex items-center gap-2" style={{ color: 'hsl(var(--text-secondary))' }}>
                  <Calendar size={14} />
                  <span>{new Date(run.timestamp).toLocaleString()}</span>
                </div>
              </td>
              <td>
                <div className="flex items-center gap-2" style={{ color: 'hsl(var(--text-secondary))' }}>
                  <FileSpreadsheet size={14} style={{ color: '#10b981' }} />
                  <span>{run.crm_filename}</span>
                </div>
              </td>
              <td style={{ color: 'hsl(var(--text-secondary))' }}>
                {run.report_count} statement(s)
              </td>
              <td className="font-semibold" style={{ color: run.match_rate_percent >= 90 ? '#10b981' : '#f59e0b' }}>
                {run.match_rate_percent.toFixed(1)}%
              </td>
              <td>
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
              </td>
              <td style={{ textAlign: 'right' }}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onViewRun(run.run_id);
                  }}
                  className="btn-secondary"
                  style={{ padding: '6px 12px', fontSize: '0.8rem', borderRadius: '6px', border: 'none' }}
                >
                  <Eye size={12} className="mr-2" />
                  <span>Drill Down</span>
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
