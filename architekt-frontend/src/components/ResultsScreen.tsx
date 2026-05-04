import { useEffect, useState } from 'react';
import { getSessionResults } from '../api/client';

type Props = {
  token: string;
  sessionId: string;
  onBackToDashboard: () => void;
};

type Results = {
  accuracy_percent: number;
  correct_count: number;
  total_questions: number;
  weak_topics: string[];
  average_response_time_ms: number | null;
  total_time_ms: number | null;
};

function getScoreMessage(pct: number): { headline: string; sub: string; color: string } {
  if (pct >= 90) return { headline: 'Outstanding!',    sub: 'You have excellent command of this material.',    color: 'text-green-400'  };
  if (pct >= 75) return { headline: 'Well done!',      sub: 'Solid performance — keep pushing.',               color: 'text-brand-400'  };
  if (pct >= 50) return { headline: 'Good effort.',    sub: 'Review the weak topics below to improve.',        color: 'text-amber-400'  };
  return          { headline: 'Needs work.',           sub: 'Focus on the flagged topics and try again.',      color: 'text-red-400'    };
}

function ScoreRing({ percent }: { percent: number }) {
  const r = 52;
  const circ = 2 * Math.PI * r;
  const offset = circ - (percent / 100) * circ;
  const color = percent >= 75 ? '#22c55e' : percent >= 50 ? '#f59e0b' : '#ef4444';

  return (
    <div className="relative w-36 h-36 mx-auto">
      <svg className="-rotate-90 w-full h-full" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={r} fill="none" stroke="#1f2638" strokeWidth="8" />
        <circle
          cx="60" cy="60" r={r} fill="none"
          stroke={color} strokeWidth="8"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold text-white tabular-nums">{Math.round(percent)}%</span>
        <span className="text-xs text-gray-500">accuracy</span>
      </div>
    </div>
  );
}

function formatTime(ms: number | null): string {
  if (ms === null) return '—';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function ResultsScreen({ token, sessionId, onBackToDashboard }: Props) {
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);
  const [results, setResults] = useState<Results | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const r = await getSessionResults(token, sessionId);
        if (!cancelled) setResults(r);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load results');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [token, sessionId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
          <span className="text-sm text-gray-500">Calculating results…</span>
        </div>
      </div>
    );
  }

  if (error) return <div className="mt-16 text-center text-red-400">{error}</div>;
  if (!results) return null;

  const msg = getScoreMessage(results.accuracy_percent);

  return (
    <div className="max-w-xl mx-auto py-10 animate-scale-in">

      {/* ── Score hero ── */}
      <div className="glass-panel p-8 mb-5 text-center">
        <ScoreRing percent={results.accuracy_percent} />
        <h2 className={`text-2xl font-bold mt-5 ${msg.color}`}>{msg.headline}</h2>
        <p className="text-sm text-gray-400 mt-1">{msg.sub}</p>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-3 mt-7 pt-6 border-t border-dark-border">
          <div>
            <p className="section-label mb-1">Score</p>
            <p className="text-xl font-bold text-white tabular-nums">
              {results.correct_count}<span className="text-gray-600 font-normal text-sm">/{results.total_questions}</span>
            </p>
          </div>
          <div>
            <p className="section-label mb-1">Avg Time</p>
            <p className="text-xl font-bold text-white tabular-nums">{formatTime(results.average_response_time_ms)}</p>
          </div>
          <div>
            <p className="section-label mb-1">Total</p>
            <p className="text-xl font-bold text-white tabular-nums">{formatTime(results.total_time_ms)}</p>
          </div>
        </div>
      </div>

      {/* ── Weak topics ── */}
      {results.weak_topics.length > 0 && (
        <div className="glass-panel p-6 mb-5 border-l-4 border-l-amber-500">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-4 h-4 text-amber-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            </svg>
            <span className="text-sm font-semibold text-amber-400">Topics to revisit</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {results.weak_topics.map((t) => (
              <span key={t} className="badge badge-amber">{t}</span>
            ))}
          </div>
        </div>
      )}

      {results.weak_topics.length === 0 && (
        <div className="glass-panel p-5 mb-5 flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-green-500/15 flex items-center justify-center shrink-0">
            <svg className="w-4 h-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <p className="text-sm text-gray-300">No weak topics detected — excellent session!</p>
        </div>
      )}

      {/* ── Actions ── */}
      <button type="button" onClick={onBackToDashboard} className="btn-primary w-full">
        Back to Dashboard
      </button>
    </div>
  );
}
