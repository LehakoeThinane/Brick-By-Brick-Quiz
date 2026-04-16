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

function normalizeOptions(options: ReviewQueueItem['options']): Array<{ key: string; text: string }> {
  if (Array.isArray(options)) {
    return options.map((o) => ({ key: String(o.key), text: String(o.text) }));
  }
  return Object.entries(options).map(([key, value]) => ({ key, text: String(value) }));
}

export function ReviewScreen({ token, onDone }: Props) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [current, setCurrent] = useState<ReviewQueueItem | null>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [answeredCount, setAnsweredCount] = useState(0);

  const questionStartRef = useRef<number | null>(null);
  const optionsList = useMemo(() => (current ? normalizeOptions(current.options) : []), [current]);

  const refreshQueue = async () => {
    const q = await getReviewQueue(token);
    const nextItems = q as unknown as ReviewQueueItem[];
    setCurrent(nextItems[0] ?? null);
    return nextItems;
  };

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        await refreshQueue();
        if (!cancelled) {
          setSelectedOption(null);
          setHasSubmitted(false);
          setIsCorrect(false);
        }
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'Failed to load review queue');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (current) questionStartRef.current = performance.now();
  }, [current?.id]);

  const submit = async () => {
    if (!current || !selectedOption || questionStartRef.current === null) return;

    const response_time_ms = Math.round(performance.now() - questionStartRef.current);
    const res = await answerReviewQueueItem(token, current.id, {
      submitted_answer: selectedOption,
      response_time_ms,
    });

    setIsCorrect(res.is_correct);
    setHasSubmitted(true);
  };

  const handleNext = async () => {
    if (!current) return;
    setHasSubmitted(false);
    setSelectedOption(null);
    setIsCorrect(false);

    const nextAnswered = answeredCount + 1;
    if (nextAnswered >= 15) {
      setAnsweredCount(nextAnswered);
      onDone();
      return;
    }

    setAnsweredCount(nextAnswered);
    const nextItems = await refreshQueue();
    if (nextItems.length === 0) onDone();
  };

  if (loading) return <div className="p-8 text-center text-gray-400">Loading review queue...</div>;
  if (error) return <div className="p-8 text-center text-red-300">{error}</div>;

  if (!current) {
    return (
      <div className="glass-panel text-center p-12 animate-fade-in max-w-2xl mx-auto mt-12">
        <h2 className="text-3xl font-bold text-white mb-4">Review Queue Empty</h2>
        <p className="text-gray-400 mb-8 max-w-sm mx-auto">Nothing to reinforce right now.</p>
        <button onClick={onDone} className="btn-primary">
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto mt-12 px-4 pb-24 animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <span className="text-sm font-semibold tracking-wider text-brand-500 uppercase">{current.subcategory ?? 'Review'}</span>
          <h2 className="text-2xl font-bold text-white mt-1">Review Question</h2>
        </div>
        <div className="text-gray-400 font-medium">{answeredCount + 1} / 15</div>
      </div>

      <div className="glass-panel p-8 mb-6">
        <p className="text-xl leading-relaxed text-gray-100 font-medium mb-8">{current.question_text}</p>

        <div className="space-y-3">
          {optionsList.map((opt) => {
            const isSelected = selectedOption === opt.key;
            const isFinished = hasSubmitted;
            const optionCorrectlyMarked = isFinished && opt.key === current.correct_answer;
            const optionWronglySelected = isFinished && isSelected && !isCorrect;

            let extraClasses = '';
            if (isFinished) {
              if (optionCorrectlyMarked) extraClasses = 'border-green-500 bg-green-500/10';
              else if (optionWronglySelected) extraClasses = 'border-red-500 bg-red-500/10 opacity-70';
              else extraClasses = 'opacity-40 cursor-not-allowed';
            }

            return (
              <button
                key={opt.key}
                disabled={isFinished}
                onClick={() => setSelectedOption(opt.key)}
                className={`option-card ${isSelected && !isFinished ? 'selected' : ''} ${extraClasses}`}
              >
                <div
                  className={`w-8 h-8 flex items-center justify-center rounded border text-sm font-bold transition-colors ${
                    isSelected && !isFinished
                      ? 'bg-brand-500 border-brand-500 text-white'
                      : optionCorrectlyMarked
                        ? 'bg-green-500 border-green-500 text-white'
                        : optionWronglySelected
                          ? 'bg-red-500 border-red-500 text-white'
                          : 'border-dark-border text-gray-400'
                  }`}
                >
                  {opt.key}
                </div>
                <span className="text-left flex-1 font-medium text-gray-200">{opt.text}</span>
              </button>
            );
          })}
        </div>
      </div>

      {!hasSubmitted ? (
        <div className="flex justify-end animate-fade-in delay-150">
          <button onClick={submit} disabled={!selectedOption} className="btn-primary">
            Submit Answer
          </button>
        </div>
      ) : (
        <EvaluationReveal
          isCorrect={isCorrect}
          explanation={current.explanation}
          correctAnswer={current.correct_answer}
          onNext={handleNext}
        />
      )}
    </div>
  );
}

