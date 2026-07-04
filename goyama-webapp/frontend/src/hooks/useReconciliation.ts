import { useState } from 'react';
import { apiService } from '../api/client';
import { useReconciliationStore } from '../store/reconciliationStore';

export const useReconciliation = () => {
  const [isRunning, setIsRunning] = useState(false);
  const { 
    crmFile, 
    reportFiles, 
    configFile, 
    setJobId, 
    setJobStatus, 
    setProgress, 
    setActiveStep,
    setError 
  } = useReconciliationStore();

  const startReconciliation = async () => {
    if (!crmFile) {
      throw new Error("CRM Master file is required.");
    }
    if (reportFiles.length === 0) {
      throw new Error("At least one report statement is required.");
    }

    setIsRunning(true);
    setError(null);
    setJobStatus('pending');
    setProgress('Submitting job...');
    setActiveStep(4); // Switch to active loader stepper step

    try {
      const crmId = crmFile.file_id;
      const reportIds = reportFiles.map(f => f.file_id);
      const configId = configFile?.file_id || null;

      const data = await apiService.runReconciliation(crmId, reportIds, configId);
      setJobId(data.job_id);
      return data.job_id;
    } catch (e: any) {
      const msg = e.response?.data?.detail || 'Failed to trigger reconciliation engine';
      setError(msg);
      setJobStatus('error');
      setActiveStep(3); // Fallback to config screen if trigger failed
      throw new Error(msg);
    } finally {
      setIsRunning(false);
    }
  };

  return {
    isRunning,
    startReconciliation
  };
};
