import React, { useEffect } from 'react';
import { useReconciliationStore } from '../../store/reconciliationStore';
import { apiService } from '../../api/client';
import { Play, History, Sparkles } from 'lucide-react';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const { 
    currentTab, 
    setCurrentTab, 
    engineHealth, 
    setEngineHealth,
    reset
  } = useReconciliationStore();

  const fetchHealth = async () => {
    try {
      const health = await apiService.getSystemHealth();
      setEngineHealth(health);
    } catch (e) {
      console.error("Failed to fetch engine health", e);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchHealth();
    // Poll health every 30 seconds
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleTabChange = (tab: 'run' | 'history' | 'demo') => {
    if (tab === 'run') {
      reset(); // Reset to upload wizard step 1
    }
    setCurrentTab(tab);
  };

  const renderHealthDot = () => {
    if (!engineHealth) return <span className="health-dot error" />;
    return <span className={`health-dot ${engineHealth.status}`} />;
  };

  const renderHealthStatus = () => {
    if (!engineHealth) return 'Offline';
    if (engineHealth.status === 'ready') return 'Ready';
    if (engineHealth.status === 'degraded') return 'Degraded';
    return 'Error';
  };

  return (
    <div className="app-shell">
      {/* Sidebar Section */}
      <aside className="sidebar">
        <div className="sidebar-top">
          {/* Logo Brand */}
          <div className="logo-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '8px', marginBottom: '28px', width: '100%' }}>
            <img src="/logo.png" alt="Goyama Logo" style={{ maxWidth: '100%', height: 'auto', maxHeight: '55px', objectFit: 'contain' }} />
            <div style={{ fontSize: '0.7rem', fontWeight: 600, color: 'hsl(var(--text-muted))', letterSpacing: '0.08em', textTransform: 'uppercase', borderTop: '1px solid hsl(var(--border-color))', width: '100%', paddingTop: '6px' }}>
              Reconciliation System
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="nav-container">
            <ul className="nav-list">
              <li>
                <button 
                  onClick={() => handleTabChange('run')}
                  className={`nav-item w-full ${currentTab === 'run' ? 'active' : ''}`}
                  style={{ background: 'none', border: 'none', textAlign: 'left' }}
                >
                  <Play size={18} />
                  <span>New Run</span>
                </button>
              </li>
              <li>
                <button 
                  onClick={() => handleTabChange('history')}
                  className={`nav-item w-full ${currentTab === 'history' ? 'active' : ''}`}
                  style={{ background: 'none', border: 'none', textAlign: 'left' }}
                >
                  <History size={18} />
                  <span>Run History</span>
                </button>
              </li>
              <li>
                <button 
                  onClick={() => handleTabChange('demo')}
                  className={`nav-item w-full ${currentTab === 'demo' ? 'active' : ''}`}
                  style={{ background: 'none', border: 'none', textAlign: 'left' }}
                >
                  <Sparkles size={18} />
                  <span>Demo Mode</span>
                </button>
              </li>
            </ul>
          </nav>
        </div>

        {/* Footer Health Indicator */}
        <div className="sidebar-bottom" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div className="health-status-badge">
            {renderHealthDot()}
            <div className="flex flex-col">
              <span className="font-medium" style={{ color: 'hsl(var(--text-primary))', fontSize: '0.8rem' }}>
                Engine Status: {renderHealthStatus()}
              </span>
              {engineHealth && (
                <span className="text-muted" style={{ fontSize: '0.7rem' }}>
                  v{engineHealth.engine_version} | Passed: {engineHealth.tests_passed}
                </span>
              )}
            </div>
          </div>
          <div style={{ textAlign: 'center', fontSize: '0.7rem', color: 'hsl(var(--text-muted))', borderTop: '1px solid hsl(var(--border-color))', paddingTop: '8px' }}>
            Version 1.0.0
          </div>
        </div>
      </aside>

      {/* Main Panel View Area */}
      <main className="main-content">
        {children}
      </main>
    </div>
  );
};
