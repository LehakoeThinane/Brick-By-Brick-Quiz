import { useEffect, useMemo, useRef, useState } from 'react';
import { ApiError, getNextQuestion, submitAnswer } from '../api/client';
import { EvaluationReveal } from './EvaluationReveal';

type Props = {
  token: string;
  sessionId: string;
  onCompleted: () => void;
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
  if (Array.isArray(options)) {
    return options.map((o) => ({ key: String(o.key), text: String(o.text) }));
  }
  return Object.entries(options).map(([key, value]) => ({ key, text: String(value) }));
}

export function QuizSession({ token, sessionId, onCompleted }: Props) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [question, setQuestion] = useState<QuizQuestion | null>(null);

  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [explanation, setExplanation] = useState<string>('');
  const [correctAnswer, setCorrectAnswer] = useState<string>('');

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
    } catch (e) {
      const err = e as ApiError;
      if (err?.status === 409) {
        onCompleted();
        return;
      }
      setError(e instanceof Error ? e.message : 'Failed to load next question');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNext();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, sessionId]);

  useEffect(() => {
    if (question) questionStartRef.current = performance.now();
  }, [question?.id]);

  const doSubmit = async () => {
    if (!question || !selectedOption || questionStartRef.current === null || hasSubmitted || isSubmitting) return;

    const response_time_ms = Math.round(performance.now() - questionStartRef.current);
    setError(null);
    setIsSubmitting(true);
    try {
      const res = await submitAnswer(token, sessionId, {
        question_id: question.id,
        question_version: question.version,
        submitted_answer: selectedOption,
        response_time_ms,
      });
      setIsCorrect(res.is_correct);
      setExplanation(res.explanation);
      setCorrectAnswer(res.correct_answer);
      setHasSubmitted(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to submit answer');
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

  if (loading) return <div className="p-8 text-center text-gray-400">Loading question...</div>;
  if (error) return <div className="p-8 text-center text-red-300">{error}</div>;
  if (!question) return <div className="p-8 text-center text-gray-400">No question available.</div>;

  return (
    <div className="max-w-3xl mx-auto mt-12 px-4 animate-fade-in pb-24">
      <div className="flex items-center justify-between mb-8">
        <div>
          <span className="text-sm font-semibold tracking-wider text-brand-500 uppercase">{question.subcategory ?? 'Quiz'}</span>
          <h2 className="text-2xl font-bold text-white mt-1">Difficulty: {question.difficulty ?? '—'}</h2>
        </div>
        <div className="text-gray-400 font-medium">
          Question {question.question_number} / {question.total_questions}
        </div>
      </div>

      <div className="glass-panel p-8 mb-6">
        <p className="text-xl leading-relaxed text-gray-100 font-medium mb-8">{question.question_text}</p>

        <div className="space-y-3">
          {optionsList.map((opt) => {
            const isSelected = selectedOption === opt.key;
            const isFinished = hasSubmitted || isSubmitting;
            const optionCorrectlyMarked = isFinished && opt.key === correctAnswer;
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
          <button onClick={doSubmit} disabled={!selectedOption || isSubmitting} className="btn-primary">
            Submit Answer
          </button>
        </div>
      ) : (
        <EvaluationReveal isCorrect={isCorrect} explanation={explanation} correctAnswer={correctAnswer} onNext={handleNext} />
      )}
    </div>
  );
}

