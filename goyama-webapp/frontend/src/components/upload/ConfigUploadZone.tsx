import React, { useRef, useState } from 'react';
import { useFileUpload } from '../../hooks/useFileUpload';
import { useReconciliationStore } from '../../store/reconciliationStore';
import { UploadCloud, CheckCircle2, Loader2, AlertCircle, Info } from 'lucide-react';
import { FileChip } from './FileChip';

export const ConfigUploadZone: React.FC = () => {
  const { configFile, setConfigFile } = useReconciliationStore();
  const { uploadConfig, isUploading, uploadError } = useFileUpload();
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
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'yaml' && ext !== 'yml') {
      alert('Unsupported file format! Please upload a .yaml or .yml configuration file.');
      return;
    }
    
    try {
      await uploadConfig(file);
    } catch (err) {
      console.error(err);
    }
  };

  const triggerSelect = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="flex flex-col gap-4">
      <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'hsl(var(--text-primary))' }}>Step 3: Upload Config YAML (Optional)</h3>
      <p className="text-sm text-muted">Upload custom comparison tolerances, fuzzy matching limits, or AMC column aliases.</p>
      
      {!configFile ? (
        <div className="flex flex-col gap-4">
          <div 
            onClick={triggerSelect}
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
            style={{ minHeight: '140px', padding: '24px' }}
          >
            <input 
              ref={fileInputRef}
              type="file"
              onChange={handleFileChange}
              accept=".yaml, .yml"
              className="file-input"
            />
            {isUploading ? (
              <>
                <Loader2 className="animate-spin" size={32} style={{ color: 'hsl(var(--primary))' }} />
                <p className="font-medium" style={{ color: 'hsl(var(--text-primary))' }}>Uploading configuration...</p>
              </>
            ) : (
              <>
                <UploadCloud size={32} style={{ color: 'hsl(var(--text-secondary))' }} />
                <p className="font-medium" style={{ color: 'hsl(var(--text-primary))' }}>
                  Drag & drop your config YAML, or <span style={{ color: 'hsl(var(--primary))', textDecoration: 'underline' }}>browse</span>
                </p>
                <p className="text-xs text-muted">Accepts YAML files (.yaml, .yml)</p>
              </>
            )}
          </div>
          
          <div className="flex items-start gap-3 card" style={{ padding: '16px', backgroundColor: 'hsl(var(--border-color) / 15%)' }}>
            <Info size={18} style={{ color: 'hsl(var(--info))', marginTop: '2px', flexShrink: 0 }} />
            <p style={{ fontSize: '0.85rem', color: 'hsl(var(--text-secondary))', lineHeight: 1.4 }}>
              <strong>Default Fallback:</strong> No configuration file selected. The engine will run using standard default settings: strict matching, 0.01 amount epsilon, and 3-day date tolerance.
            </p>
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: '20px', border: '1px solid hsl(var(--primary) / 30%)' }}>
          <div className="flex items-center gap-4">
            <div className="stage-icon done" style={{ backgroundColor: 'hsl(var(--primary) / 20%)', color: 'hsl(var(--primary))' }}>
              <CheckCircle2 size={24} />
            </div>
            <div className="flex flex-col" style={{ flexGrow: 1 }}>
              <span className="font-medium" style={{ color: 'hsl(var(--text-primary))' }}>Custom Configuration Applied</span>
              <FileChip 
                filename={configFile.filename} 
                onRemove={() => setConfigFile(null)} 
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
