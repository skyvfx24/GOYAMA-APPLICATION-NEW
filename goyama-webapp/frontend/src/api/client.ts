import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Upload endpoints
  uploadCrm: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/api/upload/crm', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  uploadReports: async (files: File[]) => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    const response = await apiClient.post('/api/upload/reports', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data; // MultiUploadResponse
  },

  uploadConfig: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/api/upload/config', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Reconciliation endpoints
  runReconciliation: async (crmId: string, reportIds: string[], configId?: string | null) => {
    const response = await apiClient.post('/api/reconciliation/run', {
      crm_id: crmId,
      report_ids: reportIds,
      config_id: configId || null,
    });
    return response.data; // {"job_id": "..."}
  },

  getJobStatus: async (jobId: string) => {
    const response = await apiClient.get(`/api/reconciliation/${jobId}`);
    return response.data; // JobStatusResponse
  },

  getJobResult: async (jobId: string) => {
    const response = await apiClient.get(`/api/reconciliation/${jobId}/result`);
    return response.data; // ReconciliationResult
  },

  // Run history endpoints
  getRuns: async () => {
    const response = await apiClient.get('/api/runs');
    return response.data; // List of runs
  },

  getRunDetails: async (runId: string) => {
    const response = await apiClient.get(`/api/runs/${runId}`);
    return response.data; // ReconciliationResult (historical)
  },

  // System health endpoints
  getSystemHealth: async () => {
    const response = await apiClient.get('/api/system/health');
    return response.data; // EngineHealthResponse
  },

  // Demo mode
  loadDemoData: async () => {
    const response = await apiClient.post('/api/demo/load');
    return response.data; // Demo load responses mapping
  },

  // Excel client/zip download URL helpers
  getClientExcelUrl: (jobId: string, pan: string) => {
    return `${API_BASE_URL}/api/reports/${jobId}/excel/client/${pan}`;
  },

  getExcelZipUrl: (jobId: string, pans: string[]) => {
    return `${API_BASE_URL}/api/reports/${jobId}/excel/zip?pans=${pans.join(',')}`;
  },
};
