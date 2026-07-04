import React from 'react';
import type { Discrepancy } from '../../types/mfrecon.types';
import { SeverityBadge } from '../dashboard/SeverityBadge';

interface ReportPreviewTableProps {
  discrepancies: Discrepancy[];
}

export const ReportPreviewTable: React.FC<ReportPreviewTableProps> = ({ discrepancies }) => {
  const getDiscrepancySource = (d: Discrepancy) => {
    const rule = d.audit_trace?.rule_evaluated || '';
    if (rule.toUpperCase().includes('CAMS')) return 'CAMS';
    if (rule.toUpperCase().includes('KFINTECH') || rule.toUpperCase().includes('KFIN')) return 'KFINTECH';
    if (rule.toUpperCase().includes('BSE')) return 'BSE';
    if (rule.toUpperCase().includes('NSE')) return 'NSE';
    if (rule.toUpperCase().includes('PDF_CAS') || rule.toUpperCase().includes('CAS')) return 'PDF CAS';
    return 'CRM';
  };

  const formatType = (type: string) => {
    return type.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
  };

  // Limit to first 20 discrepancies inside preview table
  const previewList = discrepancies.slice(0, 20);

  if (discrepancies.length === 0) {
    return (
      <div className="text-center py-6 text-sm text-muted">
        No discrepancies to preview.
      </div>
    );
  }

  return (
    <div className="table-container" style={{ borderRadius: 'var(--radius-sm)' }}>
      <table style={{ fontSize: '0.8rem' }}>
        <thead>
          <tr>
            <th style={{ padding: '10px 14px' }}>PAN</th>
            <th style={{ padding: '10px 14px' }}>Source</th>
            <th style={{ padding: '10px 14px' }}>Type</th>
            <th style={{ padding: '10px 14px' }}>Severity</th>
            <th style={{ padding: '10px 14px' }}>Details</th>
          </tr>
        </thead>
        <tbody>
          {previewList.map((d, index) => (
            <tr key={`${d.pan}-${index}`}>
              <td style={{ padding: '10px 14px', fontFamily: 'monospace', color: 'hsl(var(--text-primary))' }}>{d.pan}</td>
              <td style={{ padding: '10px 14px' }}>{getDiscrepancySource(d)}</td>
              <td style={{ padding: '10px 14px' }}>{formatType(d.discrepancy_type)}</td>
              <td style={{ padding: '10px 14px' }}><SeverityBadge severity={d.severity} /></td>
              <td style={{ padding: '10px 14px', color: 'hsl(var(--text-secondary))', fontSize: '0.75rem', maxWidth: '250px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {d.explanation}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
