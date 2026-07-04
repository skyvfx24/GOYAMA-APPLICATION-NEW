import React, { useEffect } from 'react';
import { useReconciliationStore } from '../store/reconciliationStore';
import { useRunHistory } from '../hooks/useRunHistory';
import { PageHeader } from '../components/layout/PageHeader';
import { RunHistoryTable } from '../components/history/RunHistoryTable';
import { RunHistoryCard } from '../components/history/RunHistoryCard';
import { Loader2, AlertCircle } from 'lucide-react';

export const HistoryPage: React.FC = () => {
  const { historyRuns } = useReconciliationStore();
  const { fetchHistory, loadHistoricalRun, isLoading, historyError } = useRunHistory();

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleViewRun = async (runId: string) => {
    try {
      await loadHistoricalRun(runId);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ animation: 'fadeIn 0.25s ease-out' }}>
      <PageHeader 
        title="Run History Database" 
        subtitle="Trace and revisit historical client audit reports without re-uploading file datasets."
      />

      {isLoading ? (
        <div className="card text-center" style={{ padding: '60px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
          <Loader2 className="animate-spin" size={48} style={{ color: 'hsl(var(--primary))' }} />
          <p className="text-secondary">Retrieving runs from persistent JSON storage...</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {historyError && (
            <div className="flex items-center gap-2 mt-2" style={{ color: 'hsl(var(--critical))', fontSize: '0.85rem' }}>
              <AlertCircle size={16} />
              <span>{historyError}</span>
            </div>
          )}

          {/* Desktop Table View */}
          <div className="hidden md:block">
            <RunHistoryTable runs={historyRuns} onViewRun={handleViewRun} />
          </div>

          {/* Mobile Grid Card View */}
          <div className="block md:hidden">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '16px' }}>
              {historyRuns.map((run) => (
                <RunHistoryCard 
                  key={run.run_id} 
                  run={run} 
                  onViewRun={handleViewRun} 
                />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
