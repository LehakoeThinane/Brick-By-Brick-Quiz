import { useEffect, useState } from 'react';
import { createSession, getMyProgress, getReviewQueueSummary } from '../api/client';

type Props = {
  token: string;
  displayName: string;
  onStartQuiz: (sessionId: string) => void;
  onStartReview: () => void;
};

type Topic = Awaited<ReturnType<typeof getMyProgress>>['topics'][number];

const masteryConfig: Record<string, { label: string; cls: string }> = {
  MASTERED:   { label: 'Mastered',   cls: 'badge badge-green' },
  PROFICIENT: { label: 'Proficient', cls: 'badge badge-blue'  },
  COMPETENT:  { label: 'Competent',  cls: 'badge badge-blue'  },
  DEVELOPING: { label: 'Developing', cls: 'badge badge-amber' },
  STRUGGLING: { label: 'Struggling', cls: 'badge badge-red'   },
  NOVICE:     { label: 'Novice',     cls: 'badge badge-gray'  },
};

function getMastery(state: string) {
  return masteryConfig[state] ?? { label: state, cls: 'badge badge-gray' };
}

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

function TopicRow({ topic, isStarting, onStart }: { topic: Topic; isStarting: boolean; onStart: () => void }) {
  const mastery = getMastery(topic.mastery_state);
  const accuracyPct = topic.rolling_accuracy !== null ? Math.round(topic.rolling_accuracy * 100) : 0;

  return (
    <div className="flex items-center gap-4 py-3 border-b border-dark-border last:border-0">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="font-semibold text-sm text-white truncate">{topic.category_name}</span>
          <span className={mastery.cls}>{mastery.label}</span>
        </div>
        <p className="text-xs text-gray-600 mt-0.5">
          {topic.total_attempts} attempts
          {topic.rolling_accuracy !== null && (
            <span className="text-gray-500"> · {accuracyPct}% accuracy</span>
          )}
        </p>
      </div>
      <button
        type="button"
        onClick={onStart}
        disabled={isStarting}
        className="btn-primary shrink-0 px-4 py-1.5 text-xs"
      >
        Start
      </button>
    </div>
  );
}

export function Dashboard({ token, displayName, onStartQuiz, onStartReview }: Props) {
  const [loading,       setLoading]       = useState(true);
  const [error,         setError]         = useState<string | null>(null);
  const [progress,      setProgress]      = useState<Awaited<ReturnType<typeof getMyProgress>> | null>(null);
  const [reviewSummary, setReviewSummary] = useState<Awaited<ReturnType<typeof getReviewQueueSummary>> | null>(null);
  const [isStarting,    setIsStarting]    = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [p, r] = await Promise.all([getMyProgress(token), getReviewQueueSummary(token)]);
        if (cancelled) return;
        setProgress(p);
        setReviewSummary(r);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load dashboard');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [token]);

  const startCategory = async (categoryId: string) => {
    setIsStarting(true);
    try {
      const res = await createSession(token, { mode: 'category', category_id: categoryId, total_questions: 10 });
      onStartQuiz(res.session_id);
    } finally {
      setIsStarting(false);
    }
  };

  const startAdaptive = async () => {
    setIsStarting(true);
    try {
      const res = await createSession(token, { mode: 'adaptive', category_id: null, total_questions: 10 });
      onStartQuiz(res.session_id);
    } finally {
      setIsStarting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
          <span className="text-sm text-gray-500">Loading your progress…</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-16 text-center">
        <p className="text-red-400 mb-4">{error}</p>
        <button type="button" onClick={() => window.location.reload()} className="btn-ghost">
          Retry
        </button>
      </div>
    );
  }

  if (!progress || !reviewSummary) return null;

  const weakTopics = progress.topics.filter(
    (t) => t.mastery_state === 'STRUGGLING' || t.mastery_state === 'DEVELOPING',
  );

  return (
    <div className="py-10 animate-fade-in">

      {/* ── Header ── */}
      <div className="mb-8">
        <p className="text-sm text-gray-500 mb-0.5">{getGreeting()}{displayName ? `, ${displayName}` : ''}</p>
        <h1 className="text-3xl font-bold text-white tracking-tight">Your Dashboard</h1>
      </div>

      {/* ── Stat strip ── */}
      <div className="grid grid-cols-3 gap-3 mb-8">
        <div className="glass-panel p-5 flex flex-col gap-1">
          <div className="flex items-center gap-2 mb-1">
            <svg className="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            </svg>
            <span className="section-label">Struggling</span>
          </div>
          <p className="text-3xl font-bold text-white">{progress.struggling_topics}</p>
          <p className="text-xs text-gray-600 mt-0.5">topics need work</p>
        </div>

        <div className="glass-panel p-5 flex flex-col gap-1">
          <div className="flex items-center gap-2 mb-1">
            <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="section-label">Review Queue</span>
          </div>
          <p className="text-3xl font-bold text-white">{reviewSummary.pending_items}</p>
          <p className="text-xs text-gray-600 mt-0.5">items pending</p>
        </div>

        <div className="glass-panel p-5 flex flex-col gap-1">
          <div className="flex items-center gap-2 mb-1">
            <svg className="w-4 h-4 text-brand-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <span className="section-label">Topics</span>
          </div>
          <p className="text-3xl font-bold text-white">{progress.topics.length}</p>
          <p className="text-xs text-gray-600 mt-0.5">total domains</p>
        </div>
      </div>

      {/* ── Quick actions ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-8">
        <button
          type="button"
          onClick={startAdaptive}
          disabled={isStarting}
          className="glass-panel p-5 flex items-center gap-4 text-left hover:border-brand-500/40 transition-all duration-200 group disabled:opacity-50"
        >
          <div className="w-10 h-10 rounded-xl bg-brand-500/15 flex items-center justify-center shrink-0 group-hover:bg-brand-500/25 transition-colors">
            <svg className="w-5 h-5 text-brand-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div>
            <p className="font-semibold text-white text-sm">Adaptive Mode</p>
            <p className="text-xs text-gray-500 mt-0.5">AI picks your hardest topics</p>
          </div>
          <svg className="w-4 h-4 text-gray-600 ml-auto group-hover:text-brand-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>

        <button
          type="button"
          onClick={onStartReview}
          disabled={isStarting}
          className="glass-panel p-5 flex items-center gap-4 text-left hover:border-blue-500/40 transition-all duration-200 group disabled:opacity-50"
        >
          <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center shrink-0 group-hover:bg-blue-500/20 transition-colors">
            <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </div>
          <div>
            <p className="font-semibold text-white text-sm">Review Mode</p>
            <p className="text-xs text-gray-500 mt-0.5">
              {reviewSummary.pending_items > 0
                ? `${reviewSummary.pending_items} items in your queue`
                : 'Queue is clear — great job!'}
            </p>
          </div>
          <svg className="w-4 h-4 text-gray-600 ml-auto group-hover:text-blue-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {/* ── Weak topics callout ── */}
      {weakTopics.length > 0 && (
        <div className="glass-panel p-5 mb-8 border-l-4 border-l-amber-500 animate-fade-in">
          <div className="flex items-center gap-2 mb-2">
            <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            </svg>
            <span className="text-sm font-semibold text-amber-400">Needs reinforcement</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {weakTopics.map((t) => (
              <span key={t.category_id} className="badge badge-amber">{t.category_name}</span>
            ))}
          </div>
        </div>
      )}

      {/* ── Topic list ── */}
      <div className="glass-panel p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-bold text-white">Category Practice</h2>
          <span className="section-label">{progress.topics.length} topics</span>
        </div>
        <div>
          {progress.topics.map((t) => (
            <TopicRow
              key={t.category_id}
              topic={t}
              isStarting={isStarting}
              onStart={() => startCategory(t.category_id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
