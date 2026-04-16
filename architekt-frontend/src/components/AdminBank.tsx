import React, { useEffect, useState } from 'react';

interface FlaggedQuestion {
  id: string;
  text: string;
  times_answered: number;
  correct_rate: number;
  health_indicator: 'CRITICAL';
}

export const AdminBank: React.FC = () => {
  const [flagged, setFlagged] = useState<FlaggedQuestion[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchFlagged = async () => {
      try {
        const res = await fetch('http://localhost:8000/analytics/admin/questions');
        if (res.ok) {
          const data = await res.json();
          setFlagged(data.flagged_questions);
        }
      } catch (e) {
        console.error("Could not fetch flagged questions");
      } finally {
        setIsLoading(false);
      }
    };
    fetchFlagged();
  }, []);

  return (
    <div className="max-w-6xl mx-auto mt-12 px-4 animate-fade-in pb-24">
      <header className="mb-12 flex justify-between items-end border-b border-dark-border pb-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Question Bank</h1>
          <p className="text-gray-400">Identify structural bottlenecks blocking mastery.</p>
        </div>
        <span className="bg-red-500/20 text-red-500 text-sm font-bold px-3 py-1 rounded-full">
          {flagged.length} Critical Flags
        </span>
      </header>

      {isLoading ? (
        <div className="text-gray-400 p-8 text-center glass-panel">Analyzing corpus...</div>
      ) : flagged.length === 0 ? (
        <div className="glass-panel p-12 text-center text-green-500 border-green-500/20">
          <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
          <h3 className="text-xl font-bold text-white">All Clear</h3>
          <p className="text-gray-400 mt-2">No structural bottlenecks detected across active sessions.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {flagged.map((q) => (
            <div key={q.id} className="glass-panel p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 border-l-4 border-l-red-500 relative overflow-hidden text-left bg-gradient-to-r from-red-500/5 to-transparent">
              <div className="flex-1">
                <span className="text-xs font-bold uppercase tracking-wider text-red-500 mb-2 block">
                  Sub-20% Correct Rate Flag
                </span>
                <p className="text-lg font-medium text-white">{q.text}</p>
                <div className="flex items-center gap-4 mt-3 text-sm text-gray-400">
                  <span>Tested {q.times_answered} times globally</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-gray-600"></span>
                  <span>ID: {q.id.split('-')[0]}</span>
                </div>
              </div>
              
              <div className="flex flex-col items-end gap-2 md:w-32">
                <div className="text-3xl font-bold text-red-500">{q.correct_rate}%</div>
                <div className="text-xs text-gray-400 uppercase font-semibold">Success Vol.</div>
                <button className="mt-2 text-sm bg-white/5 hover:bg-white/10 px-3 py-1.5 rounded border border-dark-border transition-colors text-white">
                  Investigate
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
