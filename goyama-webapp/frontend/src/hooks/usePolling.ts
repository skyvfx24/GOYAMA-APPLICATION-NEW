import { useEffect, useRef } from 'react';
import { apiService } from '../api/client';
import { useReconciliationStore } from '../store/reconciliationStore';

export const usePolling = (jobId: string | null, onComplete?: () => void) => {
  const { setJobStatus, setProgress, setPipelineStage, setError, setResult } = useReconciliationStore();
  const intervalRef = useRef<any>(null);

  useEffect(() => {
    if (!jobId) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    const poll = async () => {
      try {
        const data = await apiService.getJobStatus(jobId);
        setJobStatus(data.status);
        setProgress(data.progress);
        setPipelineStage(data.pipeline_stage);

        if (data.status === 'done') {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
          
          // Fetch final result and update store
          const result = await apiService.getJobResult(jobId);
          setResult(result);
          if (onComplete) onComplete();
        } else if (data.status === 'error') {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
          setError(data.error || 'Reconciliation failed due to an engine error.');
        }
      } catch (e: any) {
        logger.error('Polling error', e);
        clearInterval(intervalRef.current);
        intervalRef.current = null;
        setError(e.response?.data?.detail || 'Lost connection to the backend server.');
        setJobStatus('error');
      }
    };

    // Run first check immediately
    poll();

    // Poll every 2 seconds
    intervalRef.current = setInterval(poll, 2000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [jobId]);
};

const logger = {
  error: (msg: string, err: any) => console.error(msg, err)
};
