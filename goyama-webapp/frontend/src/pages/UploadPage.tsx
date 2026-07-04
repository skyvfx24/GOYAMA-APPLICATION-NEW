import React from 'react';
import { useReconciliationStore } from '../store/reconciliationStore';
import { useReconciliation } from '../hooks/useReconciliation';
import { usePolling } from '../hooks/usePolling';
import { PageHeader } from '../components/layout/PageHeader';
import { CRMUploadZone } from '../components/upload/CRMUploadZone';
import { ReportUploadZone } from '../components/upload/ReportUploadZone';
import { ConfigUploadZone } from '../components/upload/ConfigUploadZone';
import { PipelineStepper } from '../components/pipeline/PipelineStepper';
import { Play, ArrowRight, ArrowLeft, Loader2, AlertCircle } from 'lucide-react';

export const UploadPage: React.FC = () => {
  const { 
    activeStep, 
    setActiveStep, 
    crmFile, 
    reportFiles, 
    jobId, 
    progress,
    error,
    reset
  } = useReconciliationStore();

  const { startReconciliation, isRunning } = useReconciliation();

  // Initialize status polling if jobId is active
  usePolling(jobId);

  const steps = [
    { number: 1, label: "CRM Master" },
    { number: 2, label: "Report Statements" },
    { number: 3, label: "Configuration" },
    { number: 4, label: "Execution Trace" }
  ];

  const handleNext = () => {
    if (activeStep === 1 && !crmFile) {
      alert("Please upload the CRM Master file to proceed.");
      return;
    }
    if (activeStep === 2 && reportFiles.length === 0) {
      alert("Please upload at least one report statement file to proceed.");
      return;
    }
    if (activeStep < 3) {
      setActiveStep((activeStep + 1) as any);
    }
  };

  const handleBack = () => {
    if (activeStep > 1 && activeStep < 4) {
      setActiveStep((activeStep - 1) as any);
    }
  };

  const handleTriggerRun = async () => {
    try {
      await startReconciliation();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ animation: 'fadeIn 0.25s ease-out' }}>
      <PageHeader 
        title="Execute Reconciliation Run" 
        subtitle="Initiate E2E matching alignment against broker files and generate discrepancies."
      />

      {/* Step Stepper Header (steps 1-3 only, hide in step 4 loader) */}
      {activeStep < 4 && (
        <div className="wizard-stepper">
          {steps.slice(0, 3).map((s) => (
            <div 
              key={s.number}
              onClick={() => {
                if (s.number < activeStep) {
                  setActiveStep(s.number as any);
                } else if (s.number > activeStep) {
                  // Allow forward navigation only if files are uploaded
                  if (activeStep === 1 && crmFile && s.number === 2) {
                    setActiveStep(2);
                  } else if (activeStep === 2 && reportFiles.length > 0 && s.number === 3) {
                    setActiveStep(3);
                  } else if (crmFile && reportFiles.length > 0) {
                    setActiveStep(s.number as any);
                  }
                }
              }}
              className={`wizard-step ${activeStep === s.number ? 'active' : ''} ${activeStep > s.number ? 'completed' : ''}`}
            >
              <div className="step-indicator">
                {s.number}
              </div>
              <span className="step-label">{s.label}</span>
            </div>
          ))}
        </div>
      )}

      {/* Main Content Area */}
      <div className="mt-8">
        {activeStep === 1 && <CRMUploadZone />}
        {activeStep === 2 && <ReportUploadZone />}
        {activeStep === 3 && <ConfigUploadZone />}
        
        {activeStep === 4 && (
          <div className="card text-center" style={{ padding: '60px 40px', minHeight: '380px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="animate-spin" size={64} style={{ color: 'hsl(var(--primary))' }} />
              <h3 style={{ fontSize: '1.4rem', color: 'hsl(var(--text-primary))', marginTop: '16px' }}>Reconciliation Execution in Progress</h3>
              <p className="text-secondary" style={{ maxWidth: '500px', fontSize: '0.95rem' }}>
                {progress || 'Initializing alignment rules...'}
              </p>
            </div>
            
            {/* Display Pipeline stepper during running */}
            <div className="w-full mt-8">
              <PipelineStepper />
            </div>

            {error && (
              <div 
                className="flex items-center gap-3 card mt-8" 
                style={{ 
                  padding: '16px 24px', 
                  borderLeft: '4px solid hsl(var(--critical))', 
                  backgroundColor: 'hsl(var(--critical) / 10%)',
                  textAlign: 'left'
                }}
              >
                <AlertCircle size={24} style={{ color: 'hsl(var(--critical))', flexShrink: 0 }} />
                <div className="flex flex-col">
                  <span className="font-semibold" style={{ color: 'hsl(var(--text-primary))' }}>Reconciliation Failed</span>
                  <span className="text-sm text-secondary mt-1">{error}</span>
                </div>
                <button 
                  onClick={() => reset()} 
                  className="btn btn-secondary" 
                  style={{ marginLeft: 'auto', padding: '8px 16px', fontSize: '0.85rem' }}
                >
                  Restart Wizard
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Navigation Footer Buttons */}
      {activeStep < 4 && (
        <div 
          className="flex justify-between items-center mt-8" 
          style={{ borderTop: '1px solid hsl(var(--border-color))', paddingTop: '24px' }}
        >
          <button
            onClick={handleBack}
            disabled={activeStep === 1}
            className="btn btn-secondary"
          >
            <ArrowLeft size={16} />
            <span>Back</span>
          </button>

          {activeStep < 3 ? (
            <button
              onClick={handleNext}
              disabled={(activeStep === 1 && !crmFile) || (activeStep === 2 && reportFiles.length === 0)}
              className="btn btn-primary"
            >
              <span>Continue</span>
              <ArrowRight size={16} />
            </button>
          ) : (
            <button
              onClick={handleTriggerRun}
              disabled={!crmFile || reportFiles.length === 0 || isRunning}
              className="btn btn-primary"
              style={{ backgroundColor: 'hsl(var(--primary))', boxShadow: '0 0 20px hsl(var(--primary) / 30%)' }}
            >
              <Play size={16} />
              <span>Run Reconciliation</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
};
