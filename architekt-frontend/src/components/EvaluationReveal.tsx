import React from 'react';

interface EvaluationRevealProps {
  isCorrect: boolean;
  explanation: string;
  onNext: () => void;
  correctAnswer: string;
}

export const EvaluationReveal: React.FC<EvaluationRevealProps> = ({ 
  isCorrect, 
  explanation, 
  onNext, 
  correctAnswer 
}) => {
  return (
    <div className="animate-slide-up mt-6 p-6 rounded-2xl border bg-dark-surface/90 backdrop-blur-md shadow-2xl relative overflow-hidden">
      {/* Accent Background Glow */}
      <div className={`absolute -top-20 -right-20 w-40 h-40 rounded-full blur-[80px] opacity-20 pointer-events-none transform translate-z-0 ${isCorrect ? 'bg-green-500' : 'bg-red-500'}`}></div>
      
      <div className="flex items-center gap-3 mb-4">
        {isCorrect ? (
          <div className="flex items-center justify-center w-10 h-10 rounded-full bg-green-500/10 text-green-500">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
          </div>
        ) : (
          <div className="flex items-center justify-center w-10 h-10 rounded-full bg-red-500/10 text-red-500">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
          </div>
        )}
        <h3 className="text-xl font-bold tracking-tight text-white">
          {isCorrect ? 'Correct!' : 'Incorrect'}
        </h3>
      </div>
      
      {!isCorrect && (
        <p className="text-sm font-medium text-red-400 mb-4 bg-red-500/10 px-3 py-1.5 rounded-lg inline-block">
          The correct answer was: <span className="font-bold text-white">{correctAnswer}</span>
        </p>
      )}

      <div className="prose prose-invert max-w-none text-gray-300 text-sm leading-relaxed mb-6">
        <p>{explanation}</p>
      </div>

      <div className="flex justify-end border-t border-dark-border pt-4">
         <button onClick={onNext} className="btn-primary w-full sm:w-auto flex items-center justify-center gap-2">
           Next Question
           <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path></svg>
         </button>
      </div>
    </div>
  );
};
