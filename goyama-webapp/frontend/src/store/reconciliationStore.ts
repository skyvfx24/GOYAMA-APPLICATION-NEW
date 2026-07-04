import { create } from 'zustand';
import type { 
  UploadedFile, 
  ReconciliationSummary, 
  Discrepancy, 
  SourceBreakdown, 
  EngineHealth, 
  HistoryRunSummary 
} from '../types/mfrecon.types';

interface ReconciliationState {
  // File state
  crmFile: UploadedFile | null;
  reportFiles: UploadedFile[];
  configFile: UploadedFile | null;

  // Job running state
  jobId: string | null;
  jobStatus: 'idle' | 'uploading' | 'pending' | 'running' | 'done' | 'error';
  progress: string;
  pipelineStage: number;
  error: string | null;

  // Result state
  summary: ReconciliationSummary | null;
  discrepancies: Discrepancy[];
  sourceBreakdown: SourceBreakdown | null;
  downloadUrls: { excel: string; csv: string; json: string } | null;

  // System & History state
  engineHealth: EngineHealth | null;
  historyRuns: HistoryRunSummary[];
  selectedHistoryRunId: string | null;

  // UI state
  activeStep: 1 | 2 | 3 | 4 | 5; // 1: CRM, 2: Reports, 3: Config, 4: Loading, 5: Results
  isDemoMode: boolean;
  previewOpen: boolean;
  currentTab: 'run' | 'history' | 'demo';

  // Actions
  setCrmFile: (file: UploadedFile | null) => void;
  addReportFile: (file: UploadedFile) => void;
  removeReportFile: (fileId: string) => void;
  setConfigFile: (file: UploadedFile | null) => void;
  setJobId: (jobId: string | null) => void;
  setJobStatus: (status: 'idle' | 'uploading' | 'pending' | 'running' | 'done' | 'error') => void;
  setProgress: (progress: string) => void;
  setPipelineStage: (stage: number) => void;
  setError: (error: string | null) => void;
  setResult: (result: any) => void;
  setEngineHealth: (health: EngineHealth | null) => void;
  setHistoryRuns: (runs: HistoryRunSummary[]) => void;
  setSelectedHistoryRunId: (runId: string | null) => void;
  setActiveStep: (step: 1 | 2 | 3 | 4 | 5) => void;
  setIsDemoMode: (isDemo: boolean) => void;
  setPreviewOpen: (open: boolean) => void;
  setCurrentTab: (tab: 'run' | 'history' | 'demo') => void;
  reset: () => void;
}

const initialState = {
  crmFile: null,
  reportFiles: [],
  configFile: null,
  jobId: null,
  jobStatus: 'idle' as const,
  progress: '',
  pipelineStage: 0,
  error: null,
  summary: null,
  discrepancies: [],
  sourceBreakdown: null,
  downloadUrls: null,
  selectedHistoryRunId: null,
  activeStep: 1 as const,
  isDemoMode: false,
  previewOpen: false,
  currentTab: 'run' as const,
};

export const useReconciliationStore = create<ReconciliationState>((set) => ({
  ...initialState,
  engineHealth: null,
  historyRuns: [],

  setCrmFile: (file) => set({ crmFile: file }),
  addReportFile: (file) => set((state) => {
    // Avoid duplicates of the same file_id
    if (state.reportFiles.some(f => f.file_id === file.file_id)) return {};
    return { reportFiles: [...state.reportFiles, file] };
  }),
  removeReportFile: (fileId) => set((state) => ({
    reportFiles: state.reportFiles.filter(f => f.file_id !== fileId)
  })),
  setConfigFile: (file) => set({ configFile: file }),
  setJobId: (jobId) => set({ jobId }),
  setJobStatus: (jobStatus) => set({ jobStatus }),
  setProgress: (progress) => set({ progress }),
  setPipelineStage: (pipelineStage) => set({ pipelineStage }),
  setError: (error) => set({ error }),
  
  setResult: (result) => set({
    summary: result.summary,
    discrepancies: result.discrepancies,
    sourceBreakdown: result.source_breakdown,
    downloadUrls: result.download_urls,
    jobStatus: 'done',
    activeStep: 5,
  }),

  setEngineHealth: (engineHealth) => set({ engineHealth }),
  setHistoryRuns: (historyRuns) => set({ historyRuns }),
  setSelectedHistoryRunId: (selectedHistoryRunId) => set({ selectedHistoryRunId }),
  setActiveStep: (activeStep) => set({ activeStep }),
  setIsDemoMode: (isDemoMode) => set({ isDemoMode }),
  setPreviewOpen: (previewOpen) => set({ previewOpen }),
  setCurrentTab: (currentTab) => set({ currentTab }),
  
  reset: () => set((state) => ({
    ...initialState,
    // Keep engineHealth and historyRuns across resets
    engineHealth: state.engineHealth,
    historyRuns: state.historyRuns,
  })),
}));
