import React, { useEffect, useState } from 'react';

interface DraftQuestion {
  id: string;
  question_text: string;
  options: Record<string, string>;
  correct_answer: string;
  explanation: string;
  subcategory: string;
  difficulty: number;
}

export const AIGenerationDashboard: React.FC = () => {
  const [drafts, setDrafts] = useState<DraftQuestion[]>([]);
  const [topic, setTopic] = useState('');
  const [count, setCount] = useState(5);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoadingDrafts, setIsLoadingDrafts] = useState(true);

  const fetchDrafts = async () => {
    setIsLoadingDrafts(true);
    try {
      const res = await fetch('http://localhost:8000/admin/content/drafts');
      if (res.ok) {
        const data = await res.json();
        setDrafts(data);
      }
    } catch (e) {
      console.error("Failed to fetch drafts", e);
    } finally {
      setIsLoadingDrafts(false);
    }
  };

  useEffect(() => {
    fetchDrafts();
  }, []);

  const handleGenerate = async () => {
    if (!topic) return;
    setIsGenerating(true);
    try {
      const res = await fetch('http://localhost:8000/admin/content/ai/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, count })
      });
      if (res.ok) {
        setTopic('');
        fetchDrafts();
      }
    } catch (e) {
      console.error("Generation failed", e);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApprove = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/admin/content/drafts/${id}/approve`, {
        method: 'POST'
      });
      if (res.ok) {
        setDrafts(drafts.filter(d => d.id !== id));
      }
    } catch (e) {
      console.error("Approval failed", e);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/admin/content/drafts/${id}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        setDrafts(drafts.filter(d => d.id !== id));
      }
    } catch (e) {
      console.error("Deletion failed", e);
    }
  };

  return (
    <div className="max-w-6xl mx-auto mt-12 px-4 animate-fade-in pb-24">
      <header className="mb-12">
        <h1 className="text-3xl font-bold text-white tracking-tight">AI Content Factory</h1>
        <p className="text-gray-400 mt-2">Generate and validate curriculum materials securely.</p>
      </header>

      {/* Generation Console */}
      <div className="glass-panel p-8 mb-12 border-brand-500/20 bg-gradient-to-br from-brand-500/5 to-transparent">
        <h2 className="text-xl font-bold text-white mb-6">Generation Console</h2>
        <div className="flex flex-col md:flex-row gap-4">
          <input
            type="text"
            placeholder="Topic (e.g. Distributed Caching, Kubernetes Pods)"
            className="flex-1 bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-white focus:border-brand-500 outline-none transition-all"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
          />
          <div className="flex gap-4">
            <select 
              className="bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-white focus:border-brand-500 outline-none"
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
            >
              {[1, 3, 5, 10].map(n => <option key={n} value={n}>{n} Questions</option>)}
            </select>
            <button 
              onClick={handleGenerate}
              disabled={isGenerating || !topic}
              className="btn-primary whitespace-nowrap"
            >
              {isGenerating ? 'Drafting...' : 'Generate Drafts'}
            </button>
          </div>
        </div>
      </div>

      {/* Drafts Review Area */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">Pending Review ({drafts.length})</h2>
          <button onClick={fetchDrafts} className="text-sm text-brand-500 hover:underline">Refresh List</button>
        </div>

        {isLoadingDrafts ? (
          <div className="text-center p-12 glass-panel text-gray-400">Loading drafts...</div>
        ) : drafts.length === 0 ? (
          <div className="text-center p-12 glass-panel text-gray-500 italic">No pending drafts. Use the console above to generate content.</div>
        ) : (
          <div className="grid gap-6">
            {drafts.map((d) => (
              <div key={d.id} className="glass-panel p-8 animate-slide-up">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-widest text-brand-500">{d.subcategory}</span>
                    <h3 className="text-xl font-medium text-white mt-1">{d.question_text}</h3>
                  </div>
                  <div className="bg-dark-bg px-3 py-1 rounded text-sm text-gray-400 border border-dark-border">
                    Diff: {d.difficulty}
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4 mb-8">
                  {Object.entries(d.options).map(([key, value]) => (
                    <div key={key} className={`p-3 rounded-lg border flex items-center gap-3 ${key === d.correct_answer ? 'border-green-500/50 bg-green-500/10' : 'border-dark-border bg-white/5'}`}>
                      <span className={`w-6 h-6 rounded flex items-center justify-center text-xs font-bold ${key === d.correct_answer ? 'bg-green-500 text-white' : 'bg-dark-bg text-gray-400'}`}>
                        {key}
                      </span>
                      <span className="text-gray-300 text-sm">{String(value)}</span>
                    </div>
                  ))}
                </div>

                <div className="bg-white/5 p-4 rounded-xl border border-dark-border mb-8">
                  <h4 className="text-xs font-bold uppercase text-gray-500 mb-2">Technical Explanation</h4>
                  <p className="text-sm text-gray-300 italic">{d.explanation}</p>
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-dark-border">
                  <button 
                    onClick={() => handleDelete(d.id)}
                    className="px-4 py-2 text-sm text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                  >
                    Discard Draft
                  </button>
                  <button 
                    onClick={() => handleApprove(d.id)}
                    className="btn-primary px-8"
                  >
                    Approve & Make Live
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
