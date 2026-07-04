import React from 'react';
import { Check, Loader2, Circle, AlertCircle } from 'lucide-react';

interface PipelineStepProps {
  label: string;
  status: 'done' | 'in-progress' | 'pending' | 'error';
}

export const PipelineStep: React.FC<PipelineStepProps> = ({ label, status }) => {
  const renderIcon = () => {
    switch (status) {
      case 'done':
        return (
          <div className="stage-icon done">
            <Check size={14} />
          </div>
        );
      case 'in-progress':
        return (
          <div className="stage-icon running">
            <Loader2 size={14} className="animate-spin" />
          </div>
        );
      case 'error':
        return (
          <div className="stage-icon error" style={{ backgroundColor: 'hsl(var(--critical) / 20%)', color: 'hsl(var(--critical))' }}>
            <AlertCircle size={14} />
          </div>
        );
      case 'pending':
      default:
        return (
          <div className="stage-icon pending">
            <Circle size={10} style={{ fill: 'currentColor' }} />
          </div>
        );
    }
  };

  return (
    <div className="pipeline-stage">
      {renderIcon()}
      <span className="font-medium text-sm" style={{ color: status === 'pending' ? 'hsl(var(--text-muted))' : 'hsl(var(--text-primary))' }}>
        {label}
      </span>
    </div>
  );
};
