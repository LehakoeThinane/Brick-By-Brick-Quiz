import { useEffect, useMemo, useRef, useState } from 'react';
import { answerReviewQueueItem, getReviewQueue } from '../api/client';
import { EvaluationReveal } from './EvaluationReveal';

type Props = {
  token: string;
  onDone: () => void;
};

type ReviewQueueItem = {
  id: string;
  question_text: string;
  options: Array<{ key: string; text: string }> | Record<string, unknown>;
  correct_answer: string;
  explanation: string;
  hint: string | null;
  question_version: number;
  subcategory: string | null;
};

const REVIEW_LIMIT = 15;

function normalizeOptions(options: ReviewQueueItem['options']): Array<{ key: string; text: string }> {
  if (Array.isArray(options)) return options.map((o) => ({ key: String(o.key), text: String(o.text) }));
  return Object.entries(options).map(([key, value]) => ({ key, text: String(value) }));
}

export function ReviewScreen({ token, onDone }: Props) {
  const [loading,        setLoading]        = useState(true);
  const [error,          setError]          = useState<string | null>(null);
  const [current,        setCurrent]        = useState<ReviewQueueItem | null>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [hasSubmitted,   setHasSubmitted]   = useState(false);
  const [isCorrect,      setIsCorrect]      = useState(false);
  const [answeredCount,  setAnsweredCount]  = useState(0);
  const [responseTimeMs, setResponseTimeMs] = useState(0);

  const questionStartRef = useRef<number | null>(null);
  const optionsList = useMemo(() => (current ? normalizeOptions(current.options) : []), [current]);

  const refreshQueue = async () => {
    const q = await getReviewQueue(token);
    const items = q as unknown as ReviewQueueItem[];
    setCurrent(items[0] ?? null);
    return items;
  };

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        await refreshQueue();
        if (!cancelled) { setSelectedOption(null); setHasSubmitted(false); setIsCorrect(false); }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load review queue');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (current) questionStartRef.current = performance.now();
  }, [current?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // Keyboard: 1–4 select, Enter submits / advances
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (loading) return;
      if (hasSubmitted) { if (e.key === 'Enter') handleNext(); return; }
      const idx = parseInt(e.key) - 1;
      if (idx >= 0 && idx < optionsList.length) setSelectedOption(optionsList[idx].key);
      if (e.key === 'Enter' && selectedOption) submit();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }); // eslint-disable-line react-hooks/exhaustive-deps

  const submit = async () => {
    if (!current || !selectedOption || questionStartRef.current === null) return;
    const ms = Math.round(performance.now() - questionStartRef.current);
    const res = await answerReviewQueueItem(token, current.id, { submitted_answer: selectedOption, response_time_ms: ms });
    setIsCorrect(res.is_correct);
    setResponseTimeMs(ms);
    setHasSubmitted(true);
  };

  const handleNext = async () => {
    if (!current) return;
    setHasSubmitted(false);
    setSelectedOption(null);
    setIsCorrect(false);
    setResponseTimeMs(0);

    const next = answeredCount + 1;
    setAnsweredCount(next);

    if (next >= REVIEW_LIMIT) { onDone(); return; }
    const items = await refreshQueue();
    if (items.length === 0) onDone();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
          <span className="text-sm text-gray-500">Loading review queue…</span>
        </div>
      </div>
    );
  }

  if (error) return <div className="mt-16 text-center text-red-400">{error}</div>;

  if (!current) {
    return (
      <div className="max-w-md mx-auto text-center py-20 animate-scale-in">
        <div className="w-16 h-16 rounded-2xl bg-blue-500/10 flex items-center justify-center mx-auto mb-5">
          <svg className="w-8 h-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Queue Clear</h2>
        <p className="text-sm text-gray-500 mb-8">Nothing to reinforce right now. Come back after your next session.</p>
        <button type="button" onClick={onDone} className="btn-primary">Back to Dashboard</button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto pt-8 pb-24 animate-fade-in">

      {/* ── Review mode header ── */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onDone}
            className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Home
          </button>
          <span className="text-dark-border">|</span>
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-md bg-blue-500/15 flex items-center justify-center">
              <svg className="w-3 h-3 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </div>
            <span className="section-label text-blue-400">Review Mode</span>
            {current.subcategory && (
              <span className="text-gray-600 text-xs">· {current.subcategory}</span>
            )}
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-500">Question</p>
          <p className="text-lg font-bold text-white tabular-nums">
            {answeredCount + 1}<span className="text-gray-600 font-normal text-sm"> / {REVIEW_LIMIT}</span>
          </p>
        </div>
      </div>

      {/* ── Progress dots ── */}
      <div className="flex gap-1 mb-6">
        {Array.from({ length: REVIEW_LIMIT }, (_, i) => (
          <div
            key={i}
            className={`flex-1 h-1 rounded-full transition-colors duration-300 ${
              i < answeredCount
                ? 'bg-blue-500'
                : i === answeredCount
                  ? 'bg-blue-500/40'
                  : 'bg-dark-border'
            }`}
          />
        ))}
      </div>

      {/* ── Question card ── */}
      <div className="glass-panel p-6 sm:p-8 mb-5">
        <p className="text-lg sm:text-xl leading-relaxed text-gray-100 font-medium">
          {current.question_text}
        </p>
      </div>

      {/* ── Options ── */}
      <div className="space-y-2.5 mb-5">
        {optionsList.map((opt, idx) => {
          const isSelected  = selectedOption === opt.key;
          const isFinished  = hasSubmitted;
          const isCorrectOpt    = isFinished && opt.key === current.correct_answer;
          const isWrongSelected = isFinished && isSelected && !isCorrect;

          let extraClasses = '';
          if (isFinished) {
            if (isCorrectOpt)         extraClasses = '!border-green-500 !bg-green-500/10';
            else if (isWrongSelected) extraClasses = '!border-red-500 !bg-red-500/10 opacity-70';
            else                      extraClasses = 'opacity-40';
          }

          return (
            <button
              key={opt.key}
              type="button"
              disabled={isFinished}
              onClick={() => setSelectedOption(opt.key)}
              className={`option-card ${isSelected && !isFinished ? 'selected' : ''} ${extraClasses}`}
            >
              <div className={`w-7 h-7 shrink-0 flex items-center justify-center rounded-lg border text-xs font-bold transition-colors ${
                isSelected && !isFinished ? 'bg-blue-500 border-blue-500 text-white'
                : isCorrectOpt          ? 'bg-green-500 border-green-500 text-white'
                : isWrongSelected       ? 'bg-red-500 border-red-500 text-white'
                : 'border-dark-border-light text-gray-500'
              }`}>
                {opt.key}
              </div>
              <span className="flex-1 text-sm sm:text-base text-gray-200 font-medium">{opt.text}</span>
              {!isFinished && (
                <span className="shrink-0 text-xs text-gray-700 font-mono hidden sm:block">{idx + 1}</span>
              )}
            </button>
          );
        })}
      </div>

      {/* ── Action / feedback ── */}
      {!hasSubmitted ? (
        <div className="flex items-center justify-between">
          <p className="text-xs text-gray-700 hidden sm:block">Press 1–{optionsList.length} to select · Enter to submit</p>
          <button
            type="button"
            onClick={submit}
            disabled={!selectedOption}
            className="btn-primary ml-auto"
          >
            Submit Answer
          </button>
        </div>
      ) : (
        <EvaluationReveal
          isCorrect={isCorrect}
          explanation={current.explanation}
          correctAnswer={current.correct_answer}
          responseTimeMs={responseTimeMs}
          onNext={handleNext}
        />
      )}
    </div>
  );
}
