import React from 'react';
import type { Discrepancy } from '../../types/mfrecon.types';
import { SeverityBadge } from '../dashboard/SeverityBadge';
import { X, Calendar, FileText, Settings, ShieldAlert, Cpu } from 'lucide-react';

interface DiscrepancyDrawerProps {
  discrepancy: Discrepancy | null;
  onClose: () => void;
}

export const DiscrepancyDrawer: React.FC<DiscrepancyDrawerProps> = ({ 
  discrepancy, 
  onClose 
}) => {
  if (!discrepancy) return null;

  const {
    discrepancy_type,
    pan,
    field_name,
    crm_value,
    report_value,
    severity,
    explanation,
    source_info,
    audit_trace
  } = discrepancy;

  const formatFieldName = (name: string | null) => {
    if (!name) return 'N/A';
    return name.replace(/_/g, ' ').toUpperCase();
  };

  return (
    <>
      <div className="side-sheet-overlay" onClick={onClose} />
      <div className="side-sheet">
        {/* Drawer Header */}
        <div className="flex justify-between items-center mb-4" style={{ borderBottom: '1px solid hsl(var(--border-color))', paddingBottom: '16px' }}>
          <div className="flex flex-col gap-2">
            <span className="text-xs text-muted font-semibold uppercase tracking-wider">Discrepancy Audit Trace</span>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'hsl(var(--text-primary))' }}>
              {discrepancy_type.replace(/_/g, ' ')}
            </h2>
          </div>
          <button 
            onClick={onClose} 
            className="btn-secondary" 
            style={{ padding: '6px', border: 'none', borderRadius: '50%', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Details Fields */}
        <div className="flex flex-col gap-6 mt-4">
          {/* Severity & Field Section */}
          <div className="card flex justify-between items-center" style={{ padding: '16px 20px', backgroundColor: 'hsl(var(--bg-sidebar) / 40%)' }}>
            <div className="flex flex-col gap-1">
              <span className="text-muted" style={{ fontSize: '0.75rem' }}>Severity Level</span>
              <SeverityBadge severity={severity} />
            </div>
            {field_name && (
              <div className="flex flex-col gap-1" style={{ alignItems: 'flex-end' }}>
                <span className="text-muted" style={{ fontSize: '0.75rem' }}>Mismatch Field</span>
                <span className="font-semibold" style={{ color: 'hsl(var(--primary))', fontSize: '0.9rem' }}>
                  {formatFieldName(field_name)}
                </span>
              </div>
            )}
          </div>

          {/* Explainability Block */}
          <div className="flex flex-col gap-2">
            <h4 style={{ fontSize: '0.95rem', color: 'hsl(var(--text-primary))', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldAlert size={16} style={{ color: 'hsl(var(--critical))' }} />
              <span>Explanation Summary</span>
            </h4>
            <div 
              className="card" 
              style={{ 
                padding: '16px', 
                fontSize: '0.9rem', 
                lineHeight: '1.5', 
                color: 'hsl(var(--text-secondary))', 
                borderLeft: '4px solid hsl(var(--critical))' 
              }}
            >
              {explanation}
            </div>
          </div>

          {/* Value Comparison */}
          {field_name && (
            <div className="flex flex-col gap-2">
              <h4 style={{ fontSize: '0.95rem', color: 'hsl(var(--text-primary))' }}>Comparison Ingestion</h4>
              <div className="grid-cols-2">
                <div className="card" style={{ padding: '16px', backgroundColor: 'hsl(var(--bg-sidebar) / 20%)' }}>
                  <span className="text-muted block mb-1" style={{ fontSize: '0.75rem' }}>CRM Master Value</span>
                  <span className="font-semibold" style={{ color: 'hsl(var(--text-primary))', wordBreak: 'break-all' }}>
                    {crm_value !== null && crm_value !== 'None' ? crm_value : '—'}
                  </span>
                </div>
                <div className="card" style={{ padding: '16px', backgroundColor: 'hsl(var(--bg-sidebar) / 20%)' }}>
                  <span className="text-muted block mb-1" style={{ fontSize: '0.75rem' }}>Report Statement Value</span>
                  <span className="font-semibold" style={{ color: 'hsl(var(--text-primary))', wordBreak: 'break-all' }}>
                    {report_value !== null && report_value !== 'None' ? report_value : '—'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Source Info metadata */}
          <div className="flex flex-col gap-2">
            <h4 style={{ fontSize: '0.95rem', color: 'hsl(var(--text-primary))', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={16} style={{ color: 'hsl(var(--primary))' }} />
              <span>Report Statement File Link</span>
            </h4>
            <div className="card" style={{ padding: '16px 20px' }}>
              <div className="detail-row">
                <span className="detail-label">Permanent Account (PAN)</span>
                <span className="detail-value" style={{ fontFamily: 'monospace', color: 'hsl(var(--text-primary))' }}>{pan}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">File Origin</span>
                <span className="detail-value">{source_info?.file_name || 'N/A'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Folio Reference Number</span>
                <span className="detail-value">{source_info?.folio_number || 'N/A'}</span>
              </div>
              {source_info?.raw_row_index && (
                <div className="detail-row">
                  <span className="detail-label">Record Index / Row Number</span>
                  <span className="detail-value">{source_info.raw_row_index}</span>
                </div>
              )}
              {source_info?.crm_client_id && (
                <div className="detail-row">
                  <span className="detail-label">CRM Client Reference ID</span>
                  <span className="detail-value">{source_info.crm_client_id}</span>
                </div>
              )}
            </div>
          </div>

          {/* Engine Audit Trail */}
          <div className="flex flex-col gap-2">
            <h4 style={{ fontSize: '0.95rem', color: 'hsl(var(--text-primary))', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Cpu size={16} style={{ color: 'hsl(var(--secondary))' }} />
              <span>Decision Routing Log</span>
            </h4>
            <div className="card" style={{ padding: '16px 20px' }}>
              <div className="detail-row">
                <span className="detail-label">Matching Route Path</span>
                <span className="detail-value" style={{ color: 'hsl(var(--primary))', fontWeight: 600 }}>
                  {audit_trace?.matching_route || 'UNMATCHED'}
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Reconciler Confidence</span>
                <span className="detail-value">{(audit_trace?.match_confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Evaluation Rule Applied</span>
                <span className="detail-value">{audit_trace?.rule_evaluated || 'N/A'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">System Evaluator Engine</span>
                <span className="detail-value">mfrecon v{audit_trace?.reconciler_version || '1.0.0'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Matching Timestamp</span>
                <span className="detail-value" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Calendar size={12} style={{ marginTop: '3px' }} />
                  <span>{audit_trace?.evaluation_timestamp ? new Date(audit_trace.evaluation_timestamp).toLocaleString() : 'N/A'}</span>
                </span>
              </div>
            </div>
          </div>

          {/* Skipped Comparisons criteria list */}
          {audit_trace?.skipped_comparisons && audit_trace.skipped_comparisons.length > 0 && (
            <div className="flex flex-col gap-2">
              <h4 style={{ fontSize: '0.95rem', color: 'hsl(var(--text-primary))', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Settings size={16} style={{ color: 'hsl(var(--text-muted))' }} />
                <span>Omitted Verification Scope</span>
              </h4>
              <p className="text-sm text-muted">These fields were bypassed because the report source layout does not provide them:</p>
              <div className="flex flex-wrap gap-2 mt-1">
                {audit_trace.skipped_comparisons.map((field, idx) => (
                  <span 
                    key={idx} 
                    className="badge"
                    style={{ 
                      backgroundColor: 'hsl(var(--border-color))', 
                      color: 'hsl(var(--text-secondary))',
                      fontSize: '0.7rem' 
                    }}
                  >
                    {field.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};
