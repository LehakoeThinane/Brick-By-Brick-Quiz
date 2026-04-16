import { useEffect, useState } from 'react';
import { Dashboard } from './components/Dashboard';
import { QuizSession } from './components/QuizSession';
import { ResultsScreen } from './components/ResultsScreen';
import { ReviewScreen } from './components/ReviewScreen';
import { LoginStart } from './components/LoginStart';

type Screen = 'login' | 'dashboard' | 'quiz' | 'results' | 'review';

const TOKEN_KEY = 'architekt_token';

function App() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [screen, setScreen] = useState<Screen>(() => (localStorage.getItem(TOKEN_KEY) ? 'dashboard' : 'login'));

  useEffect(() => {
    if (!token) {
      setSessionId(null);
      setScreen('login');
      return;
    }
    if (screen === 'login') setScreen('dashboard');
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleLogout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setSessionId(null);
    setScreen('login');
  };

  return (
    <div className="min-h-screen bg-dark-bg text-gray-100 pb-20">
      <nav className="border-b border-dark-border bg-dark-surface/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center font-bold text-white">
              A
            </div>
            <span className="font-bold text-xl tracking-tight text-white uppercase">Architekt</span>
          </div>

          {token ? (
            <button onClick={handleLogout} className="text-sm font-medium text-gray-400 hover:text-white">
              Logout
            </button>
          ) : (
            <div className="text-sm font-medium text-gray-400">v1.0</div>
          )}
        </div>
      </nav>

      <main className="container mx-auto">
        {screen === 'login' && <LoginStart onSuccess={(t) => setTokenAndScreen(t, setToken, setScreen)} />}
        {screen === 'dashboard' && token && (
          <Dashboard
            token={token}
            onStartQuiz={(id) => {
              setSessionId(id);
              setScreen('quiz');
            }}
            onStartReview={() => setScreen('review')}
          />
        )}
        {screen === 'quiz' && token && sessionId && <QuizSession token={token} sessionId={sessionId} onCompleted={() => setScreen('results')} />}
        {screen === 'results' && token && sessionId && (
          <ResultsScreen token={token} sessionId={sessionId} onBackToDashboard={() => setScreen('dashboard')} />
        )}
        {screen === 'review' && token && <ReviewScreen token={token} onDone={() => setScreen('dashboard')} />}
      </main>

      <footer className="fixed bottom-0 left-0 right-0 border-t border-dark-border bg-dark-bg/80 backdrop-blur-md h-12 flex items-center justify-center text-[10px] text-gray-500 uppercase tracking-widest z-50">
        Deterministic Learning Engine &bull; ARCHITEKT v1.0
      </footer>
    </div>
  );
}

function setTokenAndScreen(t: string, setTokenFn: (v: string) => void, setScreenFn: (s: Screen) => void) {
  localStorage.setItem(TOKEN_KEY, t);
  setTokenFn(t);
  setScreenFn('dashboard');
}

export default App;
