import React, { useEffect, useState } from 'react';
import { useQuizStore } from '../store/useQuizStore';
import { initDB } from '../db';
import { EvaluationReveal } from './EvaluationReveal';

export const QuizSession: React.FC = () => {
  const { session, markQuestionStart, submitAnswer } = useQuizStore();
  const [currentQuestion, setCurrentQuestion] = useState<any>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  
  // Local temporary state purely for UX while offline. Not saved to backend DB.
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);

  useEffect(() => {
    // If we have an active session, load the current question from IDB
    const loadQuestion = async () => {
      if (!session || session.completed) return;
      
      const currentId = session.questionIds[session.currentIndex];
      const db = await initDB();
      const nextQuestion = await db.get('questions', currentId);
      
      setCurrentQuestion(nextQuestion);
      setSelectedOption(null);
      setHasSubmitted(false);
      
      // Begin exact timing measurement for Mastery Engine
      markQuestionStart();
    };

    loadQuestion();
  }, [session?.currentIndex, session?.completed]);

  if (!session) {
    return <div className="p-8 text-center text-gray-400">No active session.</div>;
  }
  
  if (session.completed) {
    return (
      <div className="glass-panel text-center p-12 animate-fade-in max-w-2xl mx-auto mt-12">
        <h2 className="text-3xl font-bold text-white mb-4">Session Complete</h2>
        <p className="text-gray-400 mb-8 max-w-sm mx-auto">
          Your offline attempts have been queued. They will automatically sync with the ARCHITEKT Mastery Engine once your connection is restored.
        </p>
        <button className="btn-primary" onClick={() => useQuizStore.getState().clearSession()}>
          Return to Dashboard
        </button>
      </div>
    );
  }

  if (!currentQuestion) return <div className="p-8 text-center">Loading...</div>;

  const handleSubmit = async () => {
    if (!selectedOption || hasSubmitted) return;
    
    // Evaluate correctness temporarily purely for visual reveal
    const evaluatedCorrect = selectedOption === currentQuestion.correct_answer;
    setIsCorrect(evaluatedCorrect);
    setHasSubmitted(true);
    
    // Submit answer payload securely to the IDB queue. The exact performance.now() delta is computed natively inside.
    await submitAnswer(currentQuestion.id, selectedOption);
  };

  return (
    <div className="max-w-3xl mx-auto mt-12 px-4 animate-fade-in pb-24">
      {/* Quiz Progress Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <span className="text-sm font-semibold tracking-wider text-brand-500 uppercase">
            {currentQuestion.subcategory}
          </span>
          <h2 className="text-2xl font-bold text-white mt-1">Difficulty: {currentQuestion.difficulty}</h2>
        </div>
        <div className="text-gray-400 font-medium font-sans">
          Question {session.currentIndex + 1} / {session.questionIds.length}
        </div>
      </div>
      
      {/* Question Card */}
      <div className="glass-panel p-8 mb-6">
        <p className="text-xl leading-relaxed text-gray-100 font-medium mb-8">
          {currentQuestion.question_text}
        </p>
        
        <div className="space-y-3">
          {Object.entries(currentQuestion.options).map(([key, value]) => {
            const isSelected = selectedOption === key;
            const isFinished = hasSubmitted;
            const OptionCorrectlyMarked = isFinished && key === currentQuestion.correct_answer;
            const OptionWronglySelected = isFinished && isSelected && !isCorrect;

            let extraClasses = '';
            if (isFinished) {
               if (OptionCorrectlyMarked) extraClasses = 'border-green-500 bg-green-500/10';
               else if (OptionWronglySelected) extraClasses = 'border-red-500 bg-red-500/10 opacity-70';
               else extraClasses = 'opacity-40 cursor-not-allowed';
            }

            return (
              <button
                key={key}
                disabled={isFinished}
                onClick={() => setSelectedOption(key)}
                className={`option-card ${isSelected && !isFinished ? 'selected' : ''} ${extraClasses}`}
              >
                <div className={`w-8 h-8 flex items-center justify-center rounded border text-sm font-bold transition-colors ${
                  isSelected && !isFinished 
                  ? 'bg-brand-500 border-brand-500 text-white' 
                  : OptionCorrectlyMarked 
                    ? 'bg-green-500 border-green-500 text-white'
                    : OptionWronglySelected
                      ? 'bg-red-500 border-red-500 text-white'
                      : 'border-dark-border text-gray-400'
                }`}>
                  {key}
                </div>
                <span className="text-left flex-1 font-medium text-gray-200">{String(value)}</span>
              </button>
            );
          })}
        </div>
      </div>

      {!hasSubmitted ? (
        <div className="flex justify-end animate-fade-in delay-150">
           <button 
             onClick={handleSubmit} 
             disabled={!selectedOption} 
             className="btn-primary"
           >
             Submit Answer
           </button>
        </div>
      ) : (
        <EvaluationReveal 
          isCorrect={isCorrect}
          explanation={currentQuestion.explanation}
          correctAnswer={currentQuestion.correct_answer}
          onNext={() => {
            // Note: Our Zustand store already moved the index forward!
            // When we clear the submission flags here, the effect hook will re-render the next question.
            setHasSubmitted(false);
            setSelectedOption(null);
          }}
        />
      )}
    </div>
  );
};
