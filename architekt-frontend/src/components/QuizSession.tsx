import { useEffect, useMemo, useRef, useState } from 'react';
import { ApiError, getNextQuestion, submitAnswer } from '../api/client';
import { EvaluationReveal } from './EvaluationReveal';

type Props = {
  token: string;
  sessionId: string;
  onCompleted: () => void;
  onExit: () => void;
};

type QuizQuestion = {
  id: string;
  version: number;
  subcategory: string | null;
  difficulty: number | null;
  question_number: number;
  total_questions: number;
  question_text: string;
  options: Array<{ key: string; text: string }> | Record<string, unknown>;
  hint: string | null;
};

function normalizeOptions(options: QuizQuestion['options']): Array<{ key: string; text: string }> {
  if (Array.isArray(options)) return options.map((o) => ({ key: String(o.key), text: String(o.text) }));
  return Object.entries(options).map(([key, value]) => ({ key, text: String(value) }));
}

function DifficultyDots({ difficulty }: { difficulty: number | null }) {
  const level = difficulty ?? 0;
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className={`w-1.5 h-1.5 rounded-full transition-colors ${i <= level ? 'bg-brand-500' : 'bg-dark-border'}`}
        />
      ))}
    </div>
  );
}

export function QuizSession({ token, sessionId, onCompleted, onExit }: Props) {
  const [loading,       setLoading]       = useState(true);
  const [error,         setError]         = useState<string | null>(null);
  const [question,      setQuestion]      = useState<QuizQuestion | null>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [hasSubmitted,  setHasSubmitted]  = useState(false);
  const [isSubmitting,  setIsSubmitting]  = useState(false);
  const [isCorrect,     setIsCorrect]     = useState(false);
  const [explanation,   setExplanation]   = useState('');
  const [correctAnswer, setCorrectAnswer] = useState('');
  const [responseTimeMs, setResponseTimeMs] = useState(0);

  const questionStartRef = useRef<number | null>(null);
  const optionsList = useMemo(() => (question ? normalizeOptions(question.options) : []), [question]);

  const loadNext = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getNextQuestion(token, sessionId);
      setQuestion({
        id: res.question.id,
        version: res.question.version,
        subcategory: res.question.subcategory,
        difficulty: res.question.difficulty,
        question_text: res.question.question_text,
        options: res.question.options,
        hint: res.question.hint,
        question_number: res.question_number,
        total_questions: res.total_questions,
      });
      setSelectedOption(null);
      setHasSubmitted(false);
      setIsCorrect(false);
      setExplanation('');
      setCorrectAnswer('');
      setResponseTimeMs(0);
    } catch (e) {
      if ((e as ApiError)?.status === 409) { onCompleted(); return; }
      setError(e instanceof Error ? e.message : 'Failed to load question');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadNext(); }, [token, sessionId]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (question) questionStartRef.current = performance.now(); }, [question?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // Keyboard shortcuts: 1–4 select options, Enter submits / advances
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (loading || isSubmitting) return;
      if (hasSubmitted) {
        if (e.key === 'Enter') handleNext();
        return;
      }
      const idx = parseInt(e.key) - 1;
      if (idx >= 0 && idx < optionsList.length) setSelectedOption(optionsList[idx].key);
      if (e.key === 'Enter' && selectedOption) doSubmit();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }); // eslint-disable-line react-hooks/exhaustive-deps

  const doSubmit = async () => {
    if (!question || !selectedOption || questionStartRef.current === null || hasSubmitted || isSubmitting) return;
    const ms = Math.round(performance.now() - questionStartRef.current);
    setIsSubmitting(true);
    setError(null);
    try {
      const res = await submitAnswer(token, sessionId, {
        question_id: question.id,
        question_version: question.version,
        submitted_answer: selectedOption,
        response_time_ms: ms,
      });
      setIsCorrect(res.is_correct);
      setExplanation(res.explanation);
      setCorrectAnswer(res.correct_answer);
      setResponseTimeMs(ms);
      setHasSubmitted(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to submit');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNext = async () => {
    setSelectedOption(null);
    setHasSubmitted(false);
    setIsSubmitting(false);
    setIsCorrect(false);
    setExplanation('');
    setCorrectAnswer('');
    await loadNext();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
          <span className="text-sm text-gray-500">Loading question…</span>
        </div>
      </div>
    );
  }

  if (error) return <div className="mt-16 text-center text-red-400">{error}</div>;
  if (!question) return null;

  return (
    <div className="max-w-2xl mx-auto pt-8 pb-24 animate-fade-in">

      {/* ── Session progress dots (one per question) ── */}
      <div className="flex gap-1 mb-6">
        {Array.from({ length: question.total_questions }, (_, i) => (
          <div
            key={i}
            className={`flex-1 h-1 rounded-full transition-colors duration-300 ${
              i < question.question_number - 1
                ? 'bg-brand-500'
                : i === question.question_number - 1
                  ? 'bg-brand-500/40'
                  : 'bg-dark-border'
            }`}
          />
        ))}
      </div>

      {/* ── Header ── */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => { if (confirm('Exit quiz and return to home?')) onExit(); }}
            className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Home
          </button>
          <span className="text-dark-border">|</span>
          <div>
            <p className="section-label">{question.subcategory ?? 'Quiz'}</p>
            <DifficultyDots difficulty={question.difficulty} />
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-500">Question</p>
          <p className="text-lg font-bold text-white tabular-nums">
            {question.question_number}<span className="text-gray-600 font-normal text-sm"> / {question.total_questions}</span>
          </p>
        </div>
      </div>

      {/* ── Question card ── */}
      <div className="glass-panel p-6 sm:p-8 mb-5">
        <p className="text-lg sm:text-xl leading-relaxed text-gray-100 font-medium">
          {question.question_text}
        </p>
      </div>

      {/* ── Options ── */}
      <div className="space-y-2.5 mb-5">
        {optionsList.map((opt, idx) => {
          const isSelected = selectedOption === opt.key;
          const isFinished = hasSubmitted || isSubmitting;
          const isCorrectOpt = isFinished && opt.key === correctAnswer;
          const isWrongSelected = isFinished && isSelected && !isCorrect;

          let extraClasses = '';
          if (isFinished) {
            if (isCorrectOpt)    extraClasses = '!border-green-500 !bg-green-500/10';
            else if (isWrongSelected) extraClasses = '!border-red-500 !bg-red-500/10 opacity-70';
            else                 extraClasses = 'opacity-40';
          }

          return (
            <button
              key={opt.key}
              type="button"
              disabled={isFinished}
              onClick={() => setSelectedOption(opt.key)}
              className={`option-card ${isSelected && !isFinished ? 'selected' : ''} ${extraClasses}`}
            >
              {/* Key badge */}
              <div className={`w-7 h-7 shrink-0 flex items-center justify-center rounded-lg border text-xs font-bold transition-colors ${
                isSelected && !isFinished  ? 'bg-brand-500 border-brand-500 text-white'
                : isCorrectOpt            ? 'bg-green-500 border-green-500 text-white'
                : isWrongSelected         ? 'bg-red-500 border-red-500 text-white'
                : 'border-dark-border-light text-gray-500'
              }`}>
                {opt.key}
              </div>
              <span className="flex-1 text-sm sm:text-base text-gray-200 font-medium">{opt.text}</span>
              {/* Keyboard hint */}
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
            onClick={doSubmit}
            disabled={!selectedOption || isSubmitting}
            className="btn-primary ml-auto"
          >
            {isSubmitting ? 'Submitting…' : 'Submit Answer'}
          </button>
        </div>
      ) : (
        <EvaluationReveal
          isCorrect={isCorrect}
          explanation={explanation}
          correctAnswer={correctAnswer}
          responseTimeMs={responseTimeMs}
          onNext={handleNext}
        />
      )}
    </div>
  );
}
