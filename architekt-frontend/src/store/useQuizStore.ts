import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { v4 as uuidv4 } from 'uuid';
import { initDB } from '../db';

// Represents an active quiz session
export interface QuizSessionState {
  sessionId: string;
  isOffline: boolean;
  questionIds: string[]; // sequencing
  currentIndex: number;
  questionStartTime: number | null; // performance.now()
  completed: boolean;
}

interface QuizStore {
  session: QuizSessionState | null;
  startOfflineSession: (categorySlug: string) => Promise<void>;
  markQuestionStart: () => void;
  submitAnswer: (questionId: string, selectedOption: string) => Promise<void>;
  clearSession: () => void;
}

export const useQuizStore = create<QuizStore>()(
  persist(
    (set, get) => ({
      session: null,

      startOfflineSession: async (categorySlug: string) => {
        const db = await initDB();
        
        // Simple fallback sequencing: Grab all cached questions for the category linearly
        // Note: For 'all categories', we can fetch from the master 'questions' store
        let cachedQuestions = [];
        if (categorySlug === 'all') {
             cachedQuestions = await db.getAll('questions');
        } else {
             const tx = db.transaction('questions', 'readonly');
             const idx = tx.store.index('by-category');
             cachedQuestions = await idx.getAll(categorySlug); // Assuming categorySlug is indexed or mapped in real production
        }

        // Shuffle simply to avoid strict linear every time
        const shuffled = cachedQuestions.sort(() => 0.5 - Math.random());
        const questionIds = shuffled.map(q => q.id).slice(0, 30); // Session max length

        set({
          session: {
            sessionId: uuidv4(),
            isOffline: true,
            questionIds,
            currentIndex: 0,
            questionStartTime: null,
            completed: false
          }
        });
      },

      markQuestionStart: () => {
        set((state) => {
          if (!state.session) return state;
          return {
            session: {
              ...state.session,
              questionStartTime: performance.now()
            }
          };
        });
      },

      submitAnswer: async (questionId: string, selectedOption: string) => {
        const state = get();
        if (!state.session || !state.session.questionStartTime) return;

        // Use performance.now() for accurate precision difference
        const endTime = performance.now();
        const response_time_ms = Math.round(endTime - state.session.questionStartTime);

        // Construct Identity & Attempt Data
        const client_attempt_id = uuidv4();
        const attemptPayload = {
          client_attempt_id,
          question_id: questionId,
          selected_option: selectedOption,
          response_time_ms,
          answered_at: new Date().toISOString(),
          sync_status: 'pending' as const
        };

        // Persist to IDB
        const db = await initDB();
        await db.put('offline_attempts', attemptPayload);

        // Move Sequence Forward
        const nextIndex = state.session.currentIndex + 1;
        const isComplete = nextIndex >= state.session.questionIds.length;

        set({
          session: {
            ...state.session,
            currentIndex: nextIndex,
            questionStartTime: null,
            completed: isComplete
          }
        });
      },

      clearSession: () => set({ session: null })
    }),
    {
      name: 'architekt-session-storage', // persist session in local browser storage
    }
  )
);
