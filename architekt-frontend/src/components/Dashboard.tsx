import { useEffect, useState } from 'react';
import { createSession, getMyProgress, getReviewQueueSummary } from '../api/client';

type Props = {
  token: string;
  onStartQuiz: (sessionId: string) => void;
  onStartReview: () => void;
};

export function Dashboard({ token, onStartQuiz, onStartReview }: Props) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<Awaited<ReturnType<typeof getMyProgress>> | null>(null);
  const [reviewSummary, setReviewSummary] = useState<Awaited<ReturnType<typeof getReviewQueueSummary>> | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [p, r] = await Promise.all([getMyProgress(token), getReviewQueueSummary(token)]);
        if (cancelled) return;
        setProgress(p);
        setReviewSummary(r);
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'Failed to load dashboard');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const startCategory = async (categoryId: string) => {
    setIsStarting(true);
    try {
      const res = await createSession(token, {
        mode: 'category',
        category_id: categoryId,
        total_questions: 10,
      });
      onStartQuiz(res.session_id);
    } finally {
      setIsStarting(false);
    }
  };

  const startAdaptive = async () => {
    setIsStarting(true);
    try {
      const res = await createSession(token, {
        mode: 'adaptive',
        category_id: null,
        total_questions: 10,
      });
      onStartQuiz(res.session_id);
    } finally {
      setIsStarting(false);
    }
  };

  const weakTopics =
    progress?.topics.filter((t) => t.mastery_state === 'STRUGGLING' || t.mastery_state === 'DEVELOPING') ?? [];

  if (loading) return <div className="p-8 text-center text-gray-400">Loading dashboard...</div>;
  if (error) return <div className="p-8 text-center text-red-300">{error}</div>;
  if (!progress || !reviewSummary) return <div className="p-8 text-center text-gray-400">No data.</div>;

  return (
    <div className="max-w-5xl mx-auto mt-12 px-4 animate-fade-in pb-24">
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-white tracking-tight">ARCHITEKT</h1>
        <p className="text-gray-400 mt-2">Deterministic Learning Engine</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <div className="glass-panel p-6 border-l-4 border-l-red-500">
          <h3 className="text-sm font-semibold text-gray-400 uppercase">Struggling Topics</h3>
          <p className="text-3xl font-bold text-white mt-2">{progress.struggling_topics}</p>
        </div>
        <div className="glass-panel p-6 border-l-4 border-l-yellow-500">
          <h3 className="text-sm font-semibold text-gray-400 uppercase">Review Backlog</h3>
          <p className="text-3xl font-bold text-white mt-2">{reviewSummary.pending_items}</p>
        </div>
        <div className="glass-panel p-6 border-l-4 border-l-brand-500">
          <h3 className="text-sm font-semibold text-gray-400 uppercase">Weak Topics</h3>
          <p className="text-3xl font-bold text-white mt-2">{weakTopics.length}</p>
        </div>
      </div>

      <div className="glass-panel p-8 mb-10">
        <h2 className="text-xl font-bold text-white mb-3">Weak Topics</h2>
        {weakTopics.length === 0 ? (
          <div className="text-gray-400">You’re doing great. Nothing is currently flagged for reinforcement.</div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {weakTopics.map((t) => (
              <span key={t.category_id} className="px-3 py-1 rounded-full bg-brand-500/10 text-brand-300 text-sm">
                {t.category_name}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-panel p-8">
          <h2 className="text-xl font-bold text-white mb-4">Category Mode</h2>
          <p className="text-gray-400 mb-6">Start a quiz session inside a single domain.</p>
          <div className="space-y-3">
            {progress.topics.map((t) => {
              const isWeak = t.mastery_state === 'STRUGGLING' || t.mastery_state === 'DEVELOPING';
              return (
                <div key={t.category_id} className="flex items-center justify-between gap-4">
                  <div>
                    <div className="font-semibold text-white">{t.category_name}</div>
                    <div className={`text-sm ${isWeak ? 'text-brand-300' : 'text-gray-400'}`}>{t.mastery_state}</div>
                  </div>
                  <button
                    onClick={() => startCategory(t.category_id)}
                    disabled={isStarting}
                    className="btn-primary px-4 py-2 disabled:opacity-50"
                  >
                    Start
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        <div className="glass-panel p-8">
          <h2 className="text-xl font-bold text-white mb-4">Session Options</h2>
          <p className="text-gray-400 mb-6">Choose how the adaptive engine selects questions.</p>

          <div className="space-y-4">
            <button onClick={startAdaptive} disabled={isStarting} className="btn-primary w-full disabled:opacity-50">
              Start Adaptive Mode
            </button>
            <button
              onClick={onStartReview}
              disabled={isStarting}
              className="w-full px-6 py-3 bg-dark-surface/50 hover:bg-white/5 border border-dark-border text-white font-medium rounded-xl transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Start Review Mode
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

