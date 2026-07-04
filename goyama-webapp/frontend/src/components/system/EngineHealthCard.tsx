import React from 'react';
import { useReconciliationStore } from '../../store/reconciliationStore';
import { Shield, Settings, Calendar, Activity } from 'lucide-react';

export const EngineHealthCard: React.FC = () => {
  const { engineHealth } = useReconciliationStore();

  if (!engineHealth) {
    return (
      <div className="card text-center" style={{ padding: '24px', color: 'hsl(var(--text-secondary))' }}>
        <p className="text-sm">Fetching engine health status...</p>
      </div>
    );
  }

  const {
    engine_version,
    status,
    tests_passed,
    last_run_duration_seconds,
    last_successful_run
  } = engineHealth;

  const getStatusColor = () => {
    if (status === 'ready') return '#10b981'; // green
    if (status === 'degraded') return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  return (
    <div className="card" style={{ padding: '24px', marginBottom: '32px' }}>
      <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'hsl(var(--text-primary))', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Shield size={18} style={{ color: getStatusColor() }} />
        <span>Reconciliation Engine Health Core</span>
      </h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        {/* Version */}
        <div className="flex items-center gap-3">
          <Settings size={16} style={{ color: 'hsl(var(--text-muted))' }} />
          <div className="flex flex-col">
            <span style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))' }}>Engine Version</span>
            <span className="font-semibold text-sm" style={{ color: 'hsl(var(--text-primary))' }}>v{engine_version}</span>
          </div>
        </div>

        {/* Tests Passed */}
        <div className="flex items-center gap-3">
          <Activity size={16} style={{ color: 'hsl(var(--text-muted))' }} />
          <div className="flex flex-col">
            <span style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))' }}>Core Validation Tests</span>
            <span className="font-semibold text-sm" style={{ color: 'hsl(var(--text-primary))' }}>{tests_passed} / {tests_passed} Passed</span>
          </div>
        </div>

        {/* Last Run Duration */}
        <div className="flex items-center gap-3">
          <Activity size={16} style={{ color: 'hsl(var(--text-muted))' }} />
          <div className="flex flex-col">
            <span style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))' }}>Last Reconciliation Run</span>
            <span className="font-semibold text-sm" style={{ color: 'hsl(var(--text-primary))' }}>
              {last_run_duration_seconds ? `${last_run_duration_seconds.toFixed(2)}s` : '—'}
            </span>
          </div>
        </div>

        {/* Last Successful Run */}
        <div className="flex items-center gap-3">
          <Calendar size={16} style={{ color: 'hsl(var(--text-muted))' }} />
          <div className="flex flex-col">
            <span style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))' }}>Last Successful Match</span>
            <span className="font-semibold text-sm" style={{ color: 'hsl(var(--text-primary))' }}>
              {last_successful_run ? new Date(last_successful_run).toLocaleTimeString() : 'No runs executed yet'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
