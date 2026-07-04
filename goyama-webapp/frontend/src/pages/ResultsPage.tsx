import React, { useState } from 'react';
import { useReconciliationStore } from '../store/reconciliationStore';
import { PageHeader } from '../components/layout/PageHeader';
import { StatGrid } from '../components/dashboard/StatGrid';
import { PipelineStepper } from '../components/pipeline/PipelineStepper';
import { SourceBreakdownChart } from '../components/analytics/SourceBreakdownChart';
import { SourceBreakdownCard } from '../components/analytics/SourceBreakdownCard';
import { DiscrepancyFilters } from '../components/discrepancy/DiscrepancyFilters';
import { DiscrepancyTable } from '../components/discrepancy/DiscrepancyTable';
import { DiscrepancyDrawer } from '../components/discrepancy/DiscrepancyDrawer';
import { DownloadPanel } from '../components/reports/DownloadPanel';
import { ReportPreviewModal } from '../components/report-preview/ReportPreviewModal';
import { EngineHealthCard } from '../components/system/EngineHealthCard';
import type { Discrepancy } from '../types/mfrecon.types';
import { RefreshCw, ShieldCheck, FolderArchive } from 'lucide-react';

export const ResultsPage: React.FC = () => {
  const { 
    summary,
    discrepancies,
    sourceBreakdown,
    selectedHistoryRunId,
    reset,
    jobId
  } = useReconciliationStore();

  const [selectedDiscrepancy, setSelectedDiscrepancy] = useState<Discrepancy | null>(null);

  // Filter local states
  const [search, setSearch] = useState('');
  const [severity, setSeverity] = useState('ALL');
  const [source, setSource] = useState('ALL');

  if (!summary) {
    return (
      <div className="card text-center" style={{ padding: '60px' }}>
        <p className="font-medium">No results loaded.</p>
        <button onClick={reset} className="btn btn-primary mt-4">
          Go back to Upload Wizard
        </button>
      </div>
    );
  }

  const getDiscrepancySource = (d: Discrepancy) => {
    const rule = d.audit_trace?.rule_evaluated || '';
    if (rule.toUpperCase().includes('CAMS')) return 'CAMS';
    if (rule.toUpperCase().includes('KFINTECH') || rule.toUpperCase().includes('KFIN')) return 'KFINTECH';
    if (rule.toUpperCase().includes('BSE')) return 'BSE';
    if (rule.toUpperCase().includes('NSE')) return 'NSE';
    if (rule.toUpperCase().includes('PDF_CAS') || rule.toUpperCase().includes('CAS')) return 'PDF_CAS';
    return 'CRM';
  };

  // Filter discrepancies dynamically in frontend
  const filteredDiscrepancies = discrepancies.filter((d) => {
    // Search query match (PAN or Explanation text)
    const matchesSearch = 
      d.pan.toLowerCase().includes(search.toLowerCase()) || 
      (d.explanation && d.explanation.toLowerCase().includes(search.toLowerCase()));
      
    // Severity select match
    const matchesSeverity = severity === 'ALL' || d.severity.toUpperCase() === severity.toUpperCase();
    
    // Source select match
    const matchesSource = source === 'ALL' || getDiscrepancySource(d).toUpperCase() === source.toUpperCase();

    return matchesSearch && matchesSeverity && matchesSource;
  });

  const runId = selectedHistoryRunId || `RUN-${(jobId || 'local').substring(0, 6).toUpperCase()}`;

  const renderBadge = () => {
    if (selectedHistoryRunId) {
      return (
        <span 
          className="badge" 
          style={{ 
            backgroundColor: 'hsl(var(--warning) / 10%)', 
            color: 'hsl(var(--warning))',
            border: '1px solid hsl(var(--warning) / 30%)',
            gap: '6px',
            display: 'inline-flex',
            alignItems: 'center',
            fontSize: '0.8rem',
            padding: '6px 12px'
          }}
        >
          <FolderArchive size={14} />
          <span>Historical Archive (Read Only)</span>
        </span>
      );
    }
    return (
      <span 
        className="badge" 
        style={{ 
          backgroundColor: 'hsl(var(--success) / 15%)', 
          color: 'hsl(var(--success))',
          border: '1px solid hsl(var(--success) / 30%)',
          gap: '6px',
          display: 'inline-flex',
          alignItems: 'center',
          fontSize: '0.8rem',
          padding: '6px 12px'
        }}
      >
        <ShieldCheck size={14} />
        <span>Live Session Complete</span>
      </span>
    );
  };

  return (
    <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
      {/* Page Header */}
      <div className="flex justify-between items-start mb-6">
        <PageHeader 
          title={`Reconciliation Results: ${runId}`} 
          subtitle="View E2E discrepancy breakdowns, source data quality coverage, and download results."
          badge={renderBadge()}
        />
        <button 
          onClick={() => reset()}
          className="btn btn-secondary"
          style={{ padding: '10px 18px', fontSize: '0.9rem' }}
        >
          <RefreshCw size={14} className="mr-2" />
          <span>New Reconciliation</span>
        </button>
      </div>

      {/* Stepper Pipeline */}
      <PipelineStepper />

      {/* Stats Cards Section */}
      <StatGrid />

      {/* Source Breakdown Section */}
      <div style={{ marginBottom: '32px' }}>
        <SourceBreakdownChart />
      </div>

      {/* Individual Source breakdowns */}
      {sourceBreakdown && (
        <div className="grid-cols-5 mb-8">
          {Object.keys(sourceBreakdown).map((sourceKey) => (
            <SourceBreakdownCard 
              key={sourceKey}
              sourceName={sourceKey}
              stats={sourceBreakdown[sourceKey]}
            />
          ))}
        </div>
      )}

      {/* System Health Status Panel */}
      <EngineHealthCard />

      {/* Discrepancy Filters & Table */}
      <div className="mt-8">
        <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'hsl(var(--text-primary))', marginBottom: '16px' }}>
          Identified Mismatches Log ({filteredDiscrepancies.length})
        </h3>
        
        <DiscrepancyFilters 
          search={search}
          setSearch={setSearch}
          severity={severity}
          setSeverity={setSeverity}
          source={source}
          setSource={setSource}
        />

        <DiscrepancyTable 
          discrepancies={filteredDiscrepancies} 
          onRowClick={(d) => setSelectedDiscrepancy(d)} 
        />
      </div>

      {/* Download Action Bar */}
      <DownloadPanel />

      {/* Drawer Explainability Sheet */}
      <DiscrepancyDrawer 
        discrepancy={selectedDiscrepancy}
        onClose={() => setSelectedDiscrepancy(null)}
      />

      {/* Report Preview Sheets Modal */}
      <ReportPreviewModal />
    </div>
  );
};
