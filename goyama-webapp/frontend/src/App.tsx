import React from 'react';
import { useReconciliationStore } from './store/reconciliationStore';
import { AppShell } from './components/layout/AppShell';
import { UploadPage } from './pages/UploadPage';
import { ResultsPage } from './pages/ResultsPage';
import { HistoryPage } from './pages/HistoryPage';
import { DemoPage } from './pages/DemoPage';

const App: React.FC = () => {
  const { currentTab, activeStep } = useReconciliationStore();

  const renderContent = () => {
    switch (currentTab) {
      case 'history':
        if (activeStep === 5) {
          return <ResultsPage />;
        }
        return <HistoryPage />;
        
      case 'demo':
        if (activeStep === 4 || activeStep === 5) {
          // Display the progress bar (step 4) or results (step 5) during demo execution
          return activeStep === 5 ? <ResultsPage /> : <UploadPage />;
        }
        return <DemoPage />;
        
      case 'run':
      default:
        if (activeStep === 5) {
          return <ResultsPage />;
        }
        return <UploadPage />;
    }
  };

  return (
    <AppShell>
      {renderContent()}
    </AppShell>
  );
};

export default App;
