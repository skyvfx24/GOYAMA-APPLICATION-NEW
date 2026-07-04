import React from 'react';

interface PageHeaderProps {
  title: string;
  subtitle: string;
  badge?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({ title, subtitle, badge }) => {
  return (
    <div className="flex justify-between items-center mb-4" style={{ width: '100%' }}>
      <div className="flex flex-col">
        <h1 className="page-title">{title}</h1>
        <p className="page-subtitle">{subtitle}</p>
      </div>
      {badge && <div className="header-badge-container">{badge}</div>}
    </div>
  );
};
