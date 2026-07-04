export interface ReconciliationSummary {
  total_crm_records: number;
  matched_records: number;
  missing_in_crm: number;
  missing_in_report: number;
  discrepancy_count: number;
  failed_files: number;
  match_rate_percent: number;
}

export interface SourceStats {
  processed: number;
  matched: number;
  discrepancies: number;
}

export interface SourceBreakdown {
  [source: string]: SourceStats;
}

export interface PipelineStage {
  stage: string;
  status: 'done' | 'in-progress' | 'pending' | 'error';
}

export interface AuditTrace {
  matching_route: string;
  match_confidence: number;
  evaluation_timestamp: string;
  reconciler_version: string;
  rule_evaluated: string;
  skipped_comparisons: string[];
}

export interface Discrepancy {
  discrepancy_type: string;
  pan: string;
  field_name: string | null;
  crm_value: string | null;
  report_value: string | null;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  explanation: string;
  source_info: {
    file_name?: string;
    raw_row_index?: string;
    folio_number?: string;
    crm_client_id?: string;
  };
  audit_trace: AuditTrace;
}

export interface FileFailure {
  file_name: string;
  source: string;
  failure_type: string;
  message: string;
}

export interface MatchedAudit {
  pan: string;
  route: string;
  confidence: number;
  source: string;
  timestamp: string;
  skipped_comparisons: string[];
}

export interface ReconciliationResult {
  job_id: string;
  run_id?: string;
  status: string;
  summary: ReconciliationSummary;
  failed_files?: FileFailure[];
  source_breakdown: SourceBreakdown;
  pipeline_stages: PipelineStage[];
  discrepancies: Discrepancy[];
  matched_audits?: MatchedAudit[];
  download_urls: {
    excel: string;
    csv: string;
    json: string;
  };
}

export interface UploadedFile {
  file_id: string;
  filename: string;
  source_type: string; // CRM, CAMS, KFINTECH, BSE, NSE, PDF_CAS, CONFIG
}

export interface JobStatus {
  job_id: string;
  status: 'idle' | 'pending' | 'running' | 'done' | 'error';
  progress: string;
  pipeline_stage: number;
  error?: string | null;
}

export interface EngineHealth {
  engine_version: string;
  status: 'ready' | 'degraded' | 'error';
  tests_passed: number;
  last_run_duration_seconds: number | null;
  last_successful_run: string | null;
}

export interface HistoryRunSummary {
  run_id: string;
  timestamp: string;
  crm_filename: string;
  report_count: number;
  match_rate_percent: number;
  discrepancy_count: number;
  status: 'success' | 'failed' | 'partial';
}
