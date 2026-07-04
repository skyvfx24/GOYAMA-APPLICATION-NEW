import React from 'react';
import { useReconciliationStore } from '../../store/reconciliationStore';
import { Eye, FileSpreadsheet, FileText, Code } from 'lucide-react';

export const DownloadPanel: React.FC = () => {
  const { downloadUrls, setPreviewOpen } = useReconciliationStore();

  if (!downloadUrls) return null;

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
    <div className="card" style={{ padding: '24px', marginTop: '32px' }}>
      <div className="flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="flex flex-col gap-1">
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'hsl(var(--text-primary))' }}>Download Reconciliation Reports</h3>
          <p className="text-sm text-muted">Stream executive workbooks, flat row database tables, or raw audit logs.</p>
        </div>
        
        <div className="flex gap-3 flex-wrap justify-end">
          {/* Preview Button */}
          <button 
            onClick={() => setPreviewOpen(true)}
            className="btn btn-secondary"
            style={{ minWidth: '150px' }}
          >
            <Eye size={16} />
            <span>Preview Report</span>
          </button>

          {/* Excel Download */}
          <button 
            onClick={() => handleDownload(downloadUrls.excel)}
            className="btn btn-primary"
            style={{ minWidth: '150px', backgroundColor: '#10b981' }} // override green for excel
          >
            <FileSpreadsheet size={16} />
            <span>Excel Workbook</span>
          </button>

          {/* CSV Download */}
          <button 
            onClick={() => handleDownload(downloadUrls.csv)}
            className="btn btn-primary"
            style={{ minWidth: '130px', backgroundColor: '#3b82f6' }} // override blue for csv
          >
            <FileText size={16} />
            <span>CSV Flat File</span>
          </button>

          {/* JSON Download */}
          <button 
            onClick={() => handleDownload(downloadUrls.json)}
            className="btn btn-primary"
            style={{ minWidth: '130px', backgroundColor: '#8b5cf6' }} // override purple for json
          >
            <Code size={16} />
            <span>JSON Audit Log</span>
          </button>
        </div>
      </div>
    </div>
  );
};
