import { useEffect, useState } from 'react';
import { getSessionResults } from '../api/client';

type Props = {
  token: string;
  sessionId: string;
  onBackToDashboard: () => void;
};

export function ResultsScreen({ token, sessionId, onBackToDashboard }: Props) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<{
    accuracy_percent: number;
    correct_count: number;
    total_questions: number;
    weak_topics: string[];
    average_response_time_ms: number | null;
    total_time_ms: number | null;
  } | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const r = await getSessionResults(token, sessionId);
        if (cancelled) return;
        setResults(r);
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'Failed to load results');
      } finally {
        if (cancelled) return;
        setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [token, sessionId]);

  return (
    <div className="max-w-3xl mx-auto mt-12 px-4 pb-24 animate-fade-in">
      <h2 className="text-3xl font-bold text-white mb-2">Results</h2>
      <p className="text-gray-400 mb-8">Your reinforcement snapshot for this session.</p>

      {loading && <div className="text-gray-400">Loading...</div>}
      {!loading && error && <div className="text-red-300 mb-4">{error}</div>}

      {!loading && results && (
        <div className="glass-panel p-8">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-6">
            <div className="p-4 border border-dark-border rounded-lg">
              <div className="text-xs uppercase text-gray-400 mb-2">Accuracy</div>
              <div className="text-3xl font-bold text-white">{results.accuracy_percent.toFixed(2)}%</div>
            </div>
            <div className="p-4 border border-dark-border rounded-lg">
              <div className="text-xs uppercase text-gray-400 mb-2">Correct</div>
              <div className="text-3xl font-bold text-white">
                {results.correct_count}/{results.total_questions}
              </div>
            </div>
            <div className="p-4 border border-dark-border rounded-lg">
              <div className="text-xs uppercase text-gray-400 mb-2">Avg Time</div>
              <div className="text-3xl font-bold text-white">
                {results.average_response_time_ms !== null ? `${results.average_response_time_ms}ms` : '—'}
              </div>
            </div>
          </div>

          <div className="border-t border-dark-border pt-6">
            <h3 className="text-sm font-semibold text-gray-300 uppercase mb-2">Weak Topics</h3>
            {results.weak_topics.length === 0 ? (
              <div className="text-gray-400">No weak topics detected yet.</div>
            ) : (
              <ul className="list-disc pl-5 text-gray-200 space-y-2">
                {results.weak_topics.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            )}
          </div>

          <div className="flex justify-end mt-8">
            <button onClick={onBackToDashboard} className="btn-primary">
              Back to Dashboard
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

