import React from 'react';
import { Trash2, FileSpreadsheet, FileText } from 'lucide-react';

interface FileChipProps {
  filename: string;
  onRemove: () => void;
}

export const FileChip: React.FC<FileChipProps> = ({ filename, onRemove }) => {
  const isExcel = filename.toLowerCase().endsWith('.xlsx') || filename.toLowerCase().endsWith('.xls');

  const renderIcon = () => {
    if (isExcel) {
      return <FileSpreadsheet size={16} style={{ color: '#10b981' }} />;
    }
    if (filename.toLowerCase().endsWith('.pdf')) {
      return <FileText size={16} style={{ color: '#ef4444' }} />;
    }
    return <FileText size={16} style={{ color: '#3b82f6' }} />;
  };

  return (
    <div className="file-chip">
      {renderIcon()}
      <span className="font-medium" style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {filename}
      </span>
      <button 
        onClick={onRemove}
        className="file-chip-remove"
        style={{ background: 'none', border: 'none' }}
        title="Remove file"
      >
        <Trash2 size={14} />
      </button>
    </div>
  );
};
