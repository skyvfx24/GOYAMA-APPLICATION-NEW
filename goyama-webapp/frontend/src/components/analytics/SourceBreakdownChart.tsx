import React from 'react';
import { useReconciliationStore } from '../../store/reconciliationStore';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend 
} from 'recharts';

// Custom tooltips inside the dark financial theme (now theme-aware)
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div 
        className="card" 
        style={{ 
          padding: '12px 16px', 
          backgroundColor: 'hsl(var(--bg-card))', 
          border: '1px solid hsl(var(--border-color))',
          fontSize: '0.85rem'
        }}
      >
        <p className="font-semibold mb-2" style={{ color: 'hsl(var(--text-primary))' }}>{label} Source Stats</p>
        {payload.map((pld: any) => (
          <div key={pld.name} className="flex justify-between gap-4 py-1" style={{ color: pld.color }}>
            <span>{pld.name}:</span>
            <span className="font-bold">{pld.value.toLocaleString()}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export const SourceBreakdownChart: React.FC = () => {
  const { sourceBreakdown } = useReconciliationStore();

  if (!sourceBreakdown) return null;

  // Transform store breakdown object into Recharts-consumable array
  const data = Object.keys(sourceBreakdown).map(sourceKey => ({
    name: sourceKey,
    Processed: sourceBreakdown[sourceKey].processed,
    Matched: sourceBreakdown[sourceKey].matched,
    Discrepancies: sourceBreakdown[sourceKey].discrepancies
  }));

  return (
    <div className="card" style={{ padding: '24px 32px' }}>
      <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'hsl(var(--text-primary))', marginBottom: '20px' }}>
        Distributor Quality & Reconciliation Coverage
      </h3>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border-color) / 40%)" vertical={false} />
            <XAxis 
              dataKey="name" 
              stroke="hsl(var(--text-secondary))" 
              fontSize={12} 
              tickLine={false} 
            />
            <YAxis 
              stroke="hsl(var(--text-secondary))" 
              fontSize={12} 
              tickLine={false} 
              axisLine={false} 
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              verticalAlign="top" 
              height={36} 
              iconType="circle" 
              iconSize={8}
              wrapperStyle={{ fontSize: '12px' }}
            />
            <Bar dataKey="Processed" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={20} />
            <Bar dataKey="Matched" fill="#10b981" radius={[4, 4, 0, 0]} barSize={20} />
            <Bar dataKey="Discrepancies" fill="#ef4444" radius={[4, 4, 0, 0]} barSize={20} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
