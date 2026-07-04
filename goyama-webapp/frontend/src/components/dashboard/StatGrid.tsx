import React from 'react';
import { useReconciliationStore } from '../../store/reconciliationStore';
import { StatCard } from './StatCard';
import { Database, CheckSquare, Percent, AlertTriangle, FileQuestion, HelpCircle } from 'lucide-react';

export const StatGrid: React.FC = () => {
  const { summary } = useReconciliationStore();

  if (!summary) return null;

  const {
    total_crm_records,
    matched_records,
    missing_in_crm,
    missing_in_report,
    discrepancy_count,
    failed_files,
    match_rate_percent
  } = summary;

  return (
    <div className="stat-grid">
      <StatCard 
        label="Total CRM Records"
        value={total_crm_records.toLocaleString()}
        icon={<Database size={20} />}
      />
      <StatCard 
        label="Matched Records"
        value={matched_records.toLocaleString()}
        icon={<CheckSquare size={20} />}
        delta={`${total_crm_records - matched_records} unmatched`}
        deltaType="neutral"
      />
      <StatCard 
        label="Match Rate"
        value={`${match_rate_percent}%`}
        icon={<Percent size={20} />}
        delta={match_rate_percent >= 90 ? "Excellent coverage" : "Requires attention"}
        deltaType={match_rate_percent >= 90 ? "positive" : "negative"}
      />
      <StatCard 
        label="Missing in CRM"
        value={missing_in_crm.toLocaleString()}
        icon={<FileQuestion size={20} />}
        delta="Found in reports only"
        deltaType={missing_in_crm > 0 ? "negative" : "positive"}
      />
      <StatCard 
        label="Missing in Report"
        value={missing_in_report.toLocaleString()}
        icon={<HelpCircle size={20} />}
        delta="Found in CRM only"
        deltaType={missing_in_report > 0 ? "negative" : "positive"}
      />
      <StatCard 
        label="Total Discrepancies"
        value={discrepancy_count.toLocaleString()}
        icon={<AlertTriangle size={20} />}
        delta={failed_files > 0 ? `${failed_files} file parse failure(s)` : "All files parsed successfully"}
        deltaType={discrepancy_count > 0 ? "negative" : "positive"}
      />
    </div>
  );
};
