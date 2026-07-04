import React from 'react';
import { Search } from 'lucide-react';

interface DiscrepancyFiltersProps {
  search: string;
  setSearch: (val: string) => void;
  severity: string;
  setSeverity: (val: string) => void;
  source: string;
  setSource: (val: string) => void;
}

export const DiscrepancyFilters: React.FC<DiscrepancyFiltersProps> = ({
  search,
  setSearch,
  severity,
  setSeverity,
  source,
  setSource
}) => {
  return (
    <div 
      className="card flex flex-col md:flex-row gap-4 items-center justify-between"
      style={{ padding: '16px 24px', marginBottom: '20px', gap: '16px' }}
    >
      {/* Search Input */}
      <div 
        className="flex items-center gap-2" 
        style={{ 
          backgroundColor: 'hsl(var(--bg-sidebar))', 
          border: '1px solid hsl(var(--border-color))',
          borderRadius: 'var(--radius-sm)',
          padding: '8px 16px',
          width: '100%',
          maxWidth: '350px'
        }}
      >
        <Search size={16} style={{ color: 'hsl(var(--text-muted))' }} />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by PAN, Investor Name..."
          style={{
            background: 'none',
            border: 'none',
            outline: 'none',
            color: 'hsl(var(--text-primary))',
            fontSize: '0.9rem',
            width: '100%'
          }}
        />
      </div>

      {/* Select Filters */}
      <div className="flex gap-4 items-center w-full md:w-auto" style={{ justifyContent: 'flex-end' }}>
        {/* Severity Filter */}
        <div className="flex flex-col gap-1">
          <label style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))', fontWeight: 500 }}>Severity</label>
          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            style={{
              backgroundColor: 'hsl(var(--bg-sidebar))',
              border: '1px solid hsl(var(--border-color))',
              color: 'hsl(var(--text-primary))',
              padding: '8px 16px',
              borderRadius: 'var(--radius-sm)',
              outline: 'none',
              fontSize: '0.9rem',
              cursor: 'pointer'
            }}
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        {/* Source Filter */}
        <div className="flex flex-col gap-1">
          <label style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))', fontWeight: 500 }}>Source</label>
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            style={{
              backgroundColor: 'hsl(var(--bg-sidebar))',
              border: '1px solid hsl(var(--border-color))',
              color: 'hsl(var(--text-primary))',
              padding: '8px 16px',
              borderRadius: 'var(--radius-sm)',
              outline: 'none',
              fontSize: '0.9rem',
              cursor: 'pointer'
            }}
          >
            <option value="ALL">All Sources</option>
            <option value="CAMS">CAMS</option>
            <option value="KFINTECH">KFintech</option>
            <option value="BSE">BSE</option>
            <option value="NSE">NSE</option>
            <option value="PDF_CAS">PDF CAS</option>
          </select>
        </div>
      </div>
    </div>
  );
};
