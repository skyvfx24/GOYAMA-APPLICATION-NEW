import React, { useState } from 'react';
import { useReconciliationStore } from '../store/reconciliationStore';
import { useReconciliation } from '../hooks/useReconciliation';
import { apiService } from '../api/client';
import { PageHeader } from '../components/layout/PageHeader';
import { Sparkles, Loader2, Play, AlertCircle } from 'lucide-react';

export const DemoPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [demoError, setDemoError] = useState<string | null>(null);
  
  const { 
    setCrmFile, 
    addReportFile, 
    setConfigFile, 
    setIsDemoMode,
    reset
  } = useReconciliationStore();

  const { startReconciliation } = useReconciliation();

  const handleRunDemo = async () => {
    setLoading(true);
    setDemoError(null);
    reset(); // Reset active job and stepper state

    try {
      // 1. Load prepackaged synthetic mock files from backend demo data
      const demoData = await apiService.loadDemoData();
      
      // 2. Set files in store
      if (demoData.crm) {
        setCrmFile({
          file_id: demoData.crm.file_id,
          filename: demoData.crm.filename,
          source_type: demoData.crm.source_type
        });
      }
      
      if (demoData.config) {
        setConfigFile({
          file_id: demoData.config.file_id,
          filename: demoData.config.filename,
          source_type: demoData.config.source_type
        });
      }
      
      if (demoData.reports) {
        demoData.reports.forEach((uploaded: any) => {
          addReportFile({
            file_id: uploaded.file_id,
            filename: uploaded.filename,
            source_type: uploaded.source_type
          });
        });
      }
      
      // 3. Mark demo mode active
      setIsDemoMode(true);
      
      // 4. Trigger reconciliation run immediately
      // This will set step to 4 (processing console stepper view)
      // and call the backend background runner
      setTimeout(async () => {
        try {
          await startReconciliation();
        } catch (e: any) {
          setDemoError(e.message || 'Failed to start demo reconciliation');
          setLoading(false);
        }
      }, 500);

    } catch (e: any) {
      const msg = e.response?.data?.detail || 'Failed to copy and stage pre-packaged demo data files';
      setDemoError(msg);
      setLoading(false);
    }
  };

  return (
    <div style={{ animation: 'fadeIn 0.25s ease-out' }}>
      <PageHeader 
        title="Interactive Sandbox Demo" 
        subtitle="Execute an E2E test reconciliation workflow in 10 seconds using deterministic, synthetic datasets."
      />

      <div className="card text-center" style={{ padding: '60px 40px', maxWidth: '650px', margin: '40px auto 0' }}>
        <div className="flex flex-col items-center gap-4">
          <div className="logo-icon animate-bounce" style={{ width: '48px', height: '48px', fontSize: '1.5rem', marginBottom: '8px' }}>
            <Sparkles size={24} />
          </div>
          <h3 style={{ fontSize: '1.3rem', color: 'hsl(var(--text-primary))' }}>Goyama Financial Reconciliation System Sandbox</h3>
          <p className="text-secondary" style={{ fontSize: '0.95rem', lineHeight: 1.6, marginTop: '8px' }}>
            Running the demo stages realistic test scenarios without uploading real client sheets. The demo creates:
          </p>
          
          <ul className="text-sm text-secondary text-left mt-2 flex flex-col gap-2" style={{ width: '100%', maxWidth: '350px', listStyleType: 'disc', paddingLeft: '20px' }}>
            <li>A clean match scenario (Ramesh Sharma)</li>
            <li>Mobile and email variances (Sita Verma)</li>
            <li>CRM record missing in AMC statements (Amit Khan)</li>
            <li>AMC record missing in CRM (Vijay Patel)</li>
            <li>INR holding balance mismatch (Anita Sen)</li>
            <li>Fuzzy name verification checks (Rohit Gupta)</li>
          </ul>

          {loading ? (
            <div className="flex items-center gap-2 mt-8 btn btn-primary" style={{ cursor: 'not-allowed' }}>
              <Loader2 className="animate-spin" size={16} />
              <span>Staging Sandbox Assets...</span>
            </div>
          ) : (
            <button 
              onClick={handleRunDemo}
              className="btn btn-primary mt-8"
              style={{ padding: '14px 32px', fontSize: '1rem', boxShadow: '0 0 20px hsl(var(--primary) / 30%)' }}
            >
              <Play size={16} className="mr-2" />
              <span>Load Demo Data & Execute</span>
            </button>
          )}

          {demoError && (
            <div className="flex items-center gap-2 mt-4" style={{ color: 'hsl(var(--critical))', fontSize: '0.85rem' }}>
              <AlertCircle size={16} />
              <span>{demoError}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
