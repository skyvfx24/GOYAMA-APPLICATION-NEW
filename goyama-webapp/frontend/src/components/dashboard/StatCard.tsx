import React from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  delta?: string;
  deltaType?: 'positive' | 'negative' | 'neutral';
}

export const StatCard: React.FC<StatCardProps> = ({ 
  label, 
  value, 
  icon, 
  delta, 
  deltaType = 'neutral' 
}) => {
  const getDeltaColor = () => {
    if (deltaType === 'positive') return '#10b981'; // green
    if (deltaType === 'negative') return '#ef4444'; // red
    return '#6b7280'; // gray
  };

  return (
    <div className="card stat-card">
      <div className="flex justify-between items-center w-full">
        <span className="stat-label">{label}</span>
        {icon && <div style={{ color: 'hsl(var(--text-secondary))' }}>{icon}</div>}
      </div>
      <div>
        <div className="stat-value">{value}</div>
        {delta && (
          <span className="text-xs font-semibold mt-2 block" style={{ color: getDeltaColor() }}>
            {delta}
          </span>
        )}
      </div>
    </div>
  );
};
