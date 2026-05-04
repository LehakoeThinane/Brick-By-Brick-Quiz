interface Props {
  isCorrect: boolean;
  explanation: string;
  correctAnswer: string;
  responseTimeMs: number;
  onNext: () => void;
}

function formatTime(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function EvaluationReveal({ isCorrect, explanation, correctAnswer, responseTimeMs, onNext }: Props) {
  return (
    <div className="animate-slide-up mt-2">

      {/* ── Status banner ── */}
      <div className={`rounded-t-2xl px-6 py-4 flex items-center justify-between ${
        isCorrect ? 'bg-green-500/15 border border-green-500/25' : 'bg-red-500/15 border border-red-500/25'
      }`}>
        <div className="flex items-center gap-3">
          {isCorrect ? (
            <div className="w-9 h-9 rounded-full bg-green-500/20 flex items-center justify-center">
              <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          ) : (
            <div className="w-9 h-9 rounded-full bg-red-500/20 flex items-center justify-center">
              <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
          )}
          <div>
            <p className={`font-bold text-base ${isCorrect ? 'text-green-400' : 'text-red-400'}`}>
              {isCorrect ? 'Correct!' : 'Incorrect'}
            </p>
            {!isCorrect && (
              <p className="text-xs text-gray-400 mt-0.5">
                Answer: <span className="font-semibold text-white">{correctAnswer}</span>
              </p>
            )}
          </div>
        </div>
        {responseTimeMs > 0 && (
          <div className="text-right">
            <p className="text-xs text-gray-600">Response time</p>
            <p className="text-sm font-semibold text-gray-300 tabular-nums">{formatTime(responseTimeMs)}</p>
          </div>
        )}
      </div>

      {/* ── Explanation ── */}
      <div className="glass-panel rounded-t-none border-t-0 px-6 py-5">
        <p className="section-label mb-2">Explanation</p>
        <p className="text-sm text-gray-300 leading-relaxed">{explanation}</p>

        <div className="flex justify-end mt-5 pt-4 border-t border-dark-border">
          <button
            type="button"
            onClick={onNext}
            className="btn-primary"
          >
            Next Question
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
