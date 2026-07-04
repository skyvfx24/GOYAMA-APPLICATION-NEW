import React, { useRef, useState } from 'react';
import { useFileUpload } from '../../hooks/useFileUpload';
import { useReconciliationStore } from '../../store/reconciliationStore';
import { UploadCloud, CheckCircle2, Loader2, AlertCircle } from 'lucide-react';
import { FileChip } from './FileChip';

export const CRMUploadZone: React.FC = () => {
  const { crmFile, setCrmFile } = useReconciliationStore();
  const { uploadCrm, isUploading, uploadError } = useFileUpload();
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
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      await processFile(file);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      await processFile(file);
    }
  };

  const processFile = async (file: File) => {
    // Validate file type
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'csv' && ext !== 'xlsx' && ext !== 'xls') {
      alert('Unsupported file format! Please upload a .csv, .xlsx, or .xls file.');
      return;
    }
    
    try {
      await uploadCrm(file);
    } catch (err) {
      console.error(err);
    }
  };

  const triggerSelect = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="flex flex-col gap-4">
      <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'hsl(var(--text-primary))' }}>Step 1: Upload CRM Master File</h3>
      <p className="text-sm text-muted">Upload the master client list containing Permanent Account Numbers (PAN) and client holdings.</p>
      
      {!crmFile ? (
        <div 
          onClick={triggerSelect}
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
          style={{ minHeight: '220px' }}
        >
          <input 
            ref={fileInputRef}
            type="file"
            onChange={handleFileChange}
            accept=".csv, .xlsx, .xls"
            className="file-input"
          />
          {isUploading ? (
            <>
              <Loader2 className="animate-spin" size={48} style={{ color: 'hsl(var(--primary))' }} />
              <p className="font-medium" style={{ color: 'hsl(var(--text-primary))' }}>Ingesting CRM Master File...</p>
              <p className="text-sm text-muted">Parsing headers and checking required schemas</p>
            </>
          ) : (
            <>
              <UploadCloud size={48} style={{ color: 'hsl(var(--text-secondary))' }} />
              <p className="font-medium" style={{ color: 'hsl(var(--text-primary))' }}>
                Drag & drop your CRM file, or <span style={{ color: 'hsl(var(--primary))', textDecoration: 'underline' }}>browse</span>
              </p>
              <p className="text-sm text-muted">Supports CSV, Excel (.xlsx, .xls)</p>
            </>
          )}
        </div>
      ) : (
        <div className="card" style={{ padding: '20px', border: '1px solid hsl(var(--success) / 30%)' }}>
          <div className="flex items-center gap-4">
            <div className="stage-icon done">
              <CheckCircle2 size={24} />
            </div>
            <div className="flex flex-col" style={{ flexGrow: 1 }}>
              <span className="font-medium" style={{ color: 'hsl(var(--text-primary))' }}>CRM Master Ingested Successfully</span>
              <FileChip 
                filename={crmFile.filename} 
                onRemove={() => setCrmFile(null)} 
              />
            </div>
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
