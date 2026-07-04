import React, { useRef, useState } from 'react';
import { useFileUpload } from '../../hooks/useFileUpload';
import { useReconciliationStore } from '../../store/reconciliationStore';
import { UploadCloud, Loader2, AlertCircle } from 'lucide-react';

export const ReportUploadZone: React.FC = () => {
  const { reportFiles, removeReportFile } = useReconciliationStore();
  const { uploadReports, isUploading, uploadError } = useFileUpload();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const files = Array.from(e.dataTransfer.files);
      await processFiles(files);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files);
      await processFiles(files);
    }
  };

  const processFiles = async (files: File[]) => {
    try {
      await uploadReports(files);
    } catch (err) {
      console.error(err);
    }
  };

  const triggerSelect = () => {
    fileInputRef.current?.click();
  };

  const getSourceTypeColor = (type: string) => {
    switch (type.toUpperCase()) {
      case 'CAMS': return '#10b981'; // Emerald
      case 'KFINTECH': return '#f59e0b'; // Amber
      case 'BSE': return '#3b82f6'; // Blue
      case 'NSE': return '#8b5cf6'; // Purple
      case 'PDF_CAS': return '#ef4444'; // Red
      case 'INSURANCE': return '#f43f5e'; // Pink/Rose
      default: return '#6b7280'; // Gray
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'hsl(var(--text-primary))' }}>Step 2: Upload Distributor & AMC Reports</h3>
      <p className="text-sm text-muted">Upload 1 or more broker sheets (Excel/CSV) or PDF account statements. The engine automatically matches their formats.</p>
      
      <div 
        onClick={triggerSelect}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
        style={{ minHeight: '180px' }}
      >
        <input 
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileChange}
          accept=".csv, .xlsx, .xls, .pdf"
          className="file-input"
        />
        {isUploading ? (
          <>
            <Loader2 className="animate-spin" size={48} style={{ color: 'hsl(var(--primary))' }} />
            <p className="font-medium" style={{ color: 'hsl(var(--text-primary))' }}>Uploading and Analyzing Reports...</p>
            <p className="text-sm text-muted">Parsing columns to identify sources (CAMS, BSE, etc.)</p>
          </>
        ) : (
          <>
            <UploadCloud size={48} style={{ color: 'hsl(var(--text-secondary))' }} />
            <p className="font-medium" style={{ color: 'hsl(var(--text-primary))' }}>
              Drag & drop report files here, or <span style={{ color: 'hsl(var(--primary))', textDecoration: 'underline' }}>browse</span>
            </p>
            <p className="text-sm text-muted">Upload CAMS, KFintech, BSE, NSE, or CAS PDF</p>
          </>
        )}
      </div>

      {reportFiles.length > 0 && (
        <div className="mt-4 flex flex-col gap-2">
          <p className="text-sm font-medium" style={{ color: 'hsl(var(--text-primary))' }}>Ingested Reports ({reportFiles.length}):</p>
          <div className="flex flex-col gap-2">
            {reportFiles.map((file) => (
              <div 
                key={file.file_id} 
                className="flex items-center justify-between card"
                style={{ padding: '12px 20px', backgroundColor: 'hsl(var(--bg-card) / 40%)' }}
              >
                <div className="flex items-center gap-2">
                  <span 
                    className="badge" 
                    style={{ 
                      backgroundColor: `${getSourceTypeColor(file.source_type)}20`, 
                      color: getSourceTypeColor(file.source_type),
                      border: `1px solid ${getSourceTypeColor(file.source_type)}40`
                    }}
                  >
                    {file.source_type}
                  </span>
                  <span className="font-medium" style={{ fontSize: '0.9rem', color: 'hsl(var(--text-primary))' }}>
                    {file.filename}
                  </span>
                </div>
                <button 
                  onClick={() => removeReportFile(file.file_id)}
                  className="btn-secondary"
                  style={{ padding: '6px 10px', fontSize: '0.8rem', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {uploadError && (
        <div className="flex items-center gap-2" style={{ color: 'hsl(var(--critical))', fontSize: '0.85rem' }}>
          <AlertCircle size={16} />
          <span>{uploadError}</span>
        </div>
      )}
    </div>
  );
};
