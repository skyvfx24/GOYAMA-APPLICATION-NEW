import React, { useState } from 'react';
import { useReconciliationStore } from '../../store/reconciliationStore';
import { ReportPreviewTable } from './ReportPreviewTable';
import { X, FileSpreadsheet, FileText, Code, AlertTriangle } from 'lucide-react';

export const ReportPreviewModal: React.FC = () => {
  const { 
    previewOpen, 
    setPreviewOpen, 
    summary, 
    discrepancies, 
    downloadUrls 
  } = useReconciliationStore();

  // Selected Tab state
  const [activeTab, setActiveTab] = useState<'summary' | 'discrepancies' | 'failed' | 'audit'>('summary');

  if (!previewOpen) return null;

  // Try to cast discrepancies or matched audits from the result object in store
  // Since we save the result in the store, we can query it directly
  const storeState = useReconciliationStore.getState();
  const failedFiles = (storeState as any).failed_files || [];
  const matchedAudits = (storeState as any).matched_audits || [];

  const handleDownload = (path: string) => {
    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const link = document.createElement('a');
    link.href = `${API_BASE_URL}${path}`;
    link.setAttribute('download', '');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ height: '650px' }}>
        {/* Header */}
        <div className="flex justify-between items-center mb-6" style={{ borderBottom: '1px solid hsl(var(--border-color))', paddingBottom: '16px', flexShrink: 0 }}>
          <div className="flex flex-col">
            <span className="text-xs text-muted font-semibold uppercase tracking-wider">Workbook Sheet Preview</span>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'hsl(var(--text-primary))' }}>Reconciliation Worksheet Summary</h2>
          </div>
          <button 
            onClick={() => setPreviewOpen(false)}
            className="btn-secondary"
            style={{ padding: '6px', border: 'none', borderRadius: '50%', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Tab Selection */}
        <div className="tab-list" style={{ flexShrink: 0 }}>
          <button 
            onClick={() => setActiveTab('summary')}
            className={`tab-trigger ${activeTab === 'summary' ? 'active' : ''}`}
          >
            Summary Sheet
          </button>
          <button 
            onClick={() => setActiveTab('discrepancies')}
            className={`tab-trigger ${activeTab === 'discrepancies' ? 'active' : ''}`}
          >
            Discrepancies Sheet ({discrepancies.length})
          </button>
          <button 
            onClick={() => setActiveTab('failed')}
            className={`tab-trigger ${activeTab === 'failed' ? 'active' : ''}`}
          >
            Failed Files ({summary?.failed_files || 0})
          </button>
          <button 
            onClick={() => setActiveTab('audit')}
            className={`tab-trigger ${activeTab === 'audit' ? 'active' : ''}`}
          >
            Matched Audits ({matchedAudits.length || 0})
          </button>
        </div>

        {/* Tab Panels */}
        <div className="tab-panel">
          {activeTab === 'summary' && summary && (
            <div className="flex flex-col gap-6" style={{ animation: 'fadeIn 0.2s ease' }}>
              <div className="card" style={{ padding: '20px', backgroundColor: 'hsl(var(--bg-sidebar) / 40%)' }}>
                <h4 className="mb-4" style={{ fontSize: '1rem', color: 'hsl(var(--text-primary))' }}>Key Statistics</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
                  <div className="detail-row">
                    <span className="detail-label">Total CRM Records</span>
                    <span className="detail-value font-medium" style={{ color: 'hsl(var(--text-primary))' }}>{summary.total_crm_records}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Matched Records</span>
                    <span className="detail-value font-medium" style={{ color: 'hsl(var(--text-primary))' }}>{summary.matched_records}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Match Rate Percentage</span>
                    <span className="detail-value font-medium" style={{ color: '#10b981' }}>{summary.match_rate_percent}%</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Total Discrepancies</span>
                    <span className="detail-value font-medium" style={{ color: 'hsl(var(--critical))' }}>{summary.discrepancy_count}</span>
                  </div>
                </div>
              </div>

              <div className="card" style={{ padding: '20px', backgroundColor: 'hsl(var(--bg-sidebar) / 40%)' }}>
                <h4 className="mb-4" style={{ fontSize: '1rem', color: 'hsl(var(--text-primary))' }}>Ingestion Audits</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
                  <div className="detail-row">
                    <span className="detail-label">Unmatched CRM Records</span>
                    <span className="detail-value">{summary.missing_in_report}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Unmatched Report Records</span>
                    <span className="detail-value">{summary.missing_in_crm}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'discrepancies' && (
            <div style={{ animation: 'fadeIn 0.2s ease' }}>
              <p className="text-sm text-muted mb-4">Showing first 20 discrepancies. Download the full report to inspect the complete list.</p>
              <ReportPreviewTable discrepancies={discrepancies} />
            </div>
          )}

          {activeTab === 'failed' && (
            <div className="flex flex-col gap-4" style={{ animation: 'fadeIn 0.2s ease' }}>
              {failedFiles.length === 0 ? (
                <div className="text-center py-12 text-sm text-muted">
                  No file ingestion errors or decryption lockouts occurred.
                </div>
              ) : (
                failedFiles.map((f: any, idx: number) => (
                  <div 
                    key={idx} 
                    className="card flex items-start gap-4" 
                    style={{ padding: '16px', borderLeft: '4px solid hsl(var(--critical))' }}
                  >
                    <AlertTriangle size={20} style={{ color: 'hsl(var(--critical))', marginTop: '2px', flexShrink: 0 }} />
                    <div className="flex flex-col">
                      <span className="font-semibold" style={{ color: 'hsl(var(--text-primary))' }}>{f.file_name}</span>
                      <span className="text-xs text-muted font-medium mt-1">
                        Source: {f.source} | Failure Type: {f.failure_type}
                      </span>
                      <span className="text-sm text-secondary mt-2">{f.message}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'audit' && (
            <div style={{ animation: 'fadeIn 0.2s ease' }}>
              {matchedAudits.length === 0 ? (
                <div className="text-center py-12 text-sm text-muted">
                  No successfully matched records found to preview.
                </div>
              ) : (
                <div className="table-container" style={{ borderRadius: 'var(--radius-sm)' }}>
                  <table style={{ fontSize: '0.8rem' }}>
                    <thead>
                      <tr>
                        <th style={{ padding: '10px 14px' }}>PAN</th>
                        <th style={{ padding: '10px 14px' }}>Source</th>
                        <th style={{ padding: '10px 14px' }}>Match Route</th>
                        <th style={{ padding: '10px 14px' }}>Confidence</th>
                        <th style={{ padding: '10px 14px' }}>Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {matchedAudits.slice(0, 20).map((audit: any, idx: number) => (
                        <tr key={idx}>
                          <td style={{ padding: '10px 14px', fontFamily: 'monospace', color: 'hsl(var(--text-primary))' }}>{audit.pan}</td>
                          <td style={{ padding: '10px 14px' }}>{audit.source}</td>
                          <td style={{ padding: '10px 14px', color: 'hsl(var(--success))', fontWeight: 600 }}>{audit.route}</td>
                          <td style={{ padding: '10px 14px' }}>{(audit.confidence * 100).toFixed(0)}%</td>
                          <td style={{ padding: '10px 14px', color: 'hsl(var(--text-muted))' }}>
                            {new Date(audit.timestamp).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Downloads */}
        {downloadUrls && (
          <div className="flex justify-end gap-3" style={{ borderTop: '1px solid hsl(var(--border-color))', paddingTop: '20px', flexShrink: 0 }}>
            <button 
              onClick={() => handleDownload(downloadUrls.excel)}
              className="btn btn-primary"
              style={{ backgroundColor: '#10b981', padding: '10px 16px', fontSize: '0.85rem' }}
            >
              <FileSpreadsheet size={14} className="mr-2" />
              <span>Download Excel</span>
            </button>
            <button 
              onClick={() => handleDownload(downloadUrls.csv)}
              className="btn btn-primary"
              style={{ backgroundColor: '#3b82f6', padding: '10px 16px', fontSize: '0.85rem' }}
            >
              <FileText size={14} className="mr-2" />
              <span>Download CSV</span>
            </button>
            <button 
              onClick={() => handleDownload(downloadUrls.json)}
              className="btn btn-primary"
              style={{ backgroundColor: '#8b5cf6', padding: '10px 16px', fontSize: '0.85rem' }}
            >
              <Code size={14} className="mr-2" />
              <span>Download JSON</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
