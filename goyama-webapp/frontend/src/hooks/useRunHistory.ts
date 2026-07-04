import { useState } from 'react';
import { apiService } from '../api/client';
import { useReconciliationStore } from '../store/reconciliationStore';

export const useRunHistory = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  
  const { setHistoryRuns, setSelectedHistoryRunId, setResult } = useReconciliationStore();

  const fetchHistory = async () => {
    setIsLoading(true);
    setHistoryError(null);
    try {
      const data = await apiService.getRuns();
      setHistoryRuns(data);
      return data;
    } catch (e: any) {
      const msg = e.response?.data?.detail || 'Failed to fetch history';
      setHistoryError(msg);
      throw new Error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const loadHistoricalRun = async (runId: string) => {
    setIsLoading(true);
    setHistoryError(null);
    try {
      const result = await apiService.getRunDetails(runId);
      // Populate result structures directly in store and toggle to step 5 (results)
      setResult(result);
      setSelectedHistoryRunId(runId);
      return result;
    } catch (e: any) {
      const msg = e.response?.data?.detail || 'Failed to load run details';
      setHistoryError(msg);
      throw new Error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    isLoading,
    historyError,
    fetchHistory,
    loadHistoricalRun
  };
};
