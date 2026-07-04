import React from 'react';

interface SeverityBadgeProps {
  severity: string;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity }) => {
  const sev = severity.toUpperCase().trim();

  const getClassName = () => {
    switch (sev) {
      case 'CRITICAL':
        return 'badge badge-critical';
      case 'HIGH':
        return 'badge badge-high';
      case 'MEDIUM':
        return 'badge badge-medium';
      case 'LOW':
        return 'badge badge-low';
      case 'INFO':
      default:
        return 'badge badge-info';
    }
  };

  return (
    <span className={getClassName()}>
      {sev}
    </span>
  );
};
