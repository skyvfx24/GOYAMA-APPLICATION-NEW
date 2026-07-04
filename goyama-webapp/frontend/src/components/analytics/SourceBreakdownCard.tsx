import React from 'react';
import type { SourceStats } from '../../types/mfrecon.types';

interface SourceBreakdownCardProps {
  sourceName: string;
  stats: SourceStats;
}

export const SourceBreakdownCard: React.FC<SourceBreakdownCardProps> = ({ 
  sourceName, 
  stats 
}) => {
  const { processed, matched, discrepancies } = stats;
  const matchRate = processed > 0 ? (matched / processed) * 100 : 100.0;
  
  const getProgressBarColor = () => {
    if (matchRate >= 95) return '#10b981'; // emerald
    if (matchRate >= 80) return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  return (
    <div className="card" style={{ padding: '20px' }}>
      <div className="flex justify-between items-center mb-4">
        <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'hsl(var(--text-primary))' }}>{sourceName}</h4>
        <span className="font-semibold text-sm" style={{ color: getProgressBarColor() }}>
          {matchRate.toFixed(1)}% Match
        </span>
      </div>

      <div className="flex flex-col gap-3">
        {/* Progress bar */}
        <div style={{ height: '6px', width: '100%', backgroundColor: 'hsl(var(--border-color))', borderRadius: '3px', overflow: 'hidden' }}>
          <div 
            style={{ 
              height: '100%', 
              width: `${matchRate}%`, 
              backgroundColor: getProgressBarColor(),
              transition: 'width 1s ease-out'
            }} 
          />
        </div>

        {/* Small stats rows */}
        <div className="flex justify-between text-xs text-muted mt-2" style={{ borderBottom: '1px solid hsl(var(--border-color) / 40%)', paddingBottom: '6px' }}>
          <span>Processed Rows</span>
          <span className="font-semibold" style={{ color: 'hsl(var(--text-primary))' }}>{processed.toLocaleString()}</span>
        </div>
        <div className="flex justify-between text-xs text-muted" style={{ borderBottom: '1px solid hsl(var(--border-color) / 40%)', paddingBottom: '6px' }}>
          <span>Reconciled (Matched)</span>
          <span className="font-semibold" style={{ color: 'hsl(var(--text-primary))' }}>{matched.toLocaleString()}</span>
        </div>
        <div className="flex justify-between text-xs text-muted">
          <span>Discrepancy Count</span>
          <span className="font-semibold" style={{ color: discrepancies > 0 ? 'hsl(var(--critical))' : 'hsl(var(--text-primary))' }}>
            {discrepancies.toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
};
