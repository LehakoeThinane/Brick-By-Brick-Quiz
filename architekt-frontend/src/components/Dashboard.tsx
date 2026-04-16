import React, { useEffect, useState } from 'react';
import { useQuizStore } from '../store/useQuizStore';
import { SyncService } from '../services/SyncService';

// Mock types
interface SystemHealth {
  struggling_topics: number;
  review_backlog: number;
  offline_backlog: number;
}

export const Dashboard: React.FC = () => {
  const { startOfflineSession } = useQuizStore();
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);

  useEffect(() => {
    // In production this hits GET /analytics/health using an interceptor with Bearer token
    const fetchHealth = async () => {
      try {
        const res = await fetch('http://localhost:8000/analytics/health');
        if (res.ok) {
          const data = await res.json();
          setHealth(data);
        }
      } catch (e) {
        console.warn("Could not fetch remote health. Falling back to local offline measurements.");
        setHealth({ struggling_topics: 0, review_backlog: 0, offline_backlog: 0 }); // Fallback
      }
    };
    fetchHealth();
  }, []);

  const handleManualSync = async () => {
    setIsSyncing(true);
    await SyncService.flushPendingAttempts();
    setIsSyncing(false);
    // Re-fetch health to see backlog drop
    try {
      const res = await fetch('http://localhost:8000/analytics/health');
      if (res.ok) setHealth(await res.json());
    } catch(e) {}
  };

  return (
    <div className="max-w-5xl mx-auto mt-12 px-4 animate-fade-in pb-24">
      <header className="mb-12">
        <h1 className="text-4xl font-bold text-white tracking-tight">ARCHITEKT</h1>
        <p className="text-gray-400 mt-2">Technical Mastery Engine</p>
      </header>
      
      {/* Observability Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div className="glass-panel p-6 border-l-4 border-l-red-500">
          <h3 className="text-sm font-semibold text-gray-400 uppercase">Struggling Topics</h3>
          <p className="text-3xl font-bold text-white mt-2">{health ? health.struggling_topics : '...'}</p>
        </div>
        <div className="glass-panel p-6 border-l-4 border-l-yellow-500">
          <h3 className="text-sm font-semibold text-gray-400 uppercase">Review Backlog</h3>
          <p className="text-3xl font-bold text-white mt-2">{health ? health.review_backlog : '...'}</p>
        </div>
        <div className="glass-panel p-6 border-l-4 border-l-brand-500 flex justify-between items-start">
          <div>
            <h3 className="text-sm font-semibold text-gray-400 uppercase">Local Outbox</h3>
            <p className="text-3xl font-bold text-white mt-2">{health ? health.offline_backlog : '...'}</p>
          </div>
          {health && health.offline_backlog > 0 && (
             <button 
                onClick={handleManualSync} 
                disabled={isSyncing}
                className="text-xs bg-brand-500/20 text-brand-500 hover:bg-brand-500/30 px-3 py-1.5 rounded disabled:opacity-50"
             >
               {isSyncing ? 'Syncing...' : 'Sync Now'}
             </button>
          )}
        </div>
      </div>
      
      {/* Session Triggers */}
      <div className="glass-panel p-8 text-center flex flex-col items-center">
        <div className="w-16 h-16 bg-brand-500/10 text-brand-500 rounded-full flex items-center justify-center mb-6">
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Begin Offline Quiz</h2>
        <p className="text-gray-400 mb-8 max-w-sm">
          A hyper-focused structural session. Your timings and answers will be cached securely and synchronized later.
        </p>
        <button 
          onClick={() => startOfflineSession('all')} 
          className="btn-primary w-full max-w-xs"
        >
          Start Mixed Session
        </button>
      </div>
    </div>
  );
};
