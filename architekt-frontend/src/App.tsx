import React, { useState, useEffect } from 'react';
import { Dashboard } from './components/Dashboard';
import { QuizSession } from './components/QuizSession';
import { AdminBank } from './components/AdminBank';
import { AIGenerationDashboard } from './components/AIGenerationDashboard';
import { SyncService } from './services/SyncService';
import { useQuizStore } from './store/useQuizStore';

function App() {
  const [view, setView] = useState<'dashboard' | 'quiz' | 'admin' | 'ai-factory'>('dashboard');
  const { session } = useQuizStore();

  useEffect(() => {
    // Register the background sync listeners for PWA connectivity
    SyncService.registerListeners();
    // Flush immediately on load if online
    SyncService.flushPendingAttempts();
  }, []);

  // Sync view with store session
  useEffect(() => {
    if (session && !session.completed) {
      setView('quiz');
    }
  }, [session]);

  const renderView = () => {
    switch (view) {
      case 'dashboard':
        return <Dashboard />;
      case 'quiz':
        return <QuizSession />;
      case 'admin':
        return <AdminBank />;
      case 'ai-factory':
        return <AIGenerationDashboard />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-dark-bg text-gray-100 pb-20">
      {/* Navigation Bar */}
      <nav className="border-b border-dark-border bg-dark-surface/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div 
            className="flex items-center gap-2 cursor-pointer group" 
            onClick={() => setView('dashboard')}
          >
            <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center font-bold text-white group-hover:rotate-12 transition-transform">
              A
            </div>
            <span className="font-bold text-xl tracking-tight text-white uppercase">Architekt</span>
          </div>

          <div className="flex items-center gap-6">
            <button 
              onClick={() => setView('dashboard')}
              className={`text-sm font-medium transition-colors ${view === 'dashboard' ? 'text-brand-500' : 'text-gray-400 hover:text-white'}`}
            >
              Learn
            </button>
            <button 
              onClick={() => setView('admin')}
              className={`text-sm font-medium transition-colors ${view === 'admin' ? 'text-brand-500' : 'text-gray-400 hover:text-white'}`}
            >
              Observability
            </button>
            <button 
              onClick={() => setView('ai-factory')}
              className={`text-sm font-medium transition-colors ${view === 'ai-factory' ? 'text-brand-500' : 'text-gray-400 hover:text-white'}`}
            >
              Factory
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="container mx-auto">
        {renderView()}
      </main>

      {/* Footer / Status Bar */}
      <footer className="fixed bottom-0 left-0 right-0 border-t border-dark-border bg-dark-bg/80 backdrop-blur-md h-12 flex items-center justify-center text-[10px] text-gray-500 uppercase tracking-widest z-50">
        Deterministic Learning Engine &bull; ARCHITEKT v1.0 &bull; Local IDB Enabled
      </footer>
    </div>
  );
}

export default App;
