import { useEffect, useState } from 'react';
import { Dashboard } from './components/Dashboard';
import { QuizSession } from './components/QuizSession';
import { ResultsScreen } from './components/ResultsScreen';
import { ReviewScreen } from './components/ReviewScreen';
import { LoginStart } from './components/LoginStart';
import { getMe } from './api/client';

type Screen = 'login' | 'dashboard' | 'quiz' | 'results' | 'review';

const TOKEN_KEY = 'architekt_token';
const NAME_KEY  = 'architekt_name';

function App() {
  const [token,       setToken]       = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [displayName, setDisplayName] = useState<string>(() => localStorage.getItem(NAME_KEY) ?? '');
  const [sessionId,   setSessionId]   = useState<string | null>(null);
  const [screen,      setScreen]      = useState<Screen>(() => (localStorage.getItem(TOKEN_KEY) ? 'dashboard' : 'login'));

  // Hydrate display name on load if we already have a token
  useEffect(() => {
    if (token && !displayName) {
      getMe(token)
        .then((me) => {
          const name = me.display_name ?? me.email.split('@')[0];
          setDisplayName(name);
          localStorage.setItem(NAME_KEY, name);
        })
        .catch(() => {});
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!token) {
      setSessionId(null);
      setScreen('login');
    } else if (screen === 'login') {
      setScreen('dashboard');
    }
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleAuthSuccess = async (t: string) => {
    localStorage.setItem(TOKEN_KEY, t);
    setToken(t);
    try {
      const me = await getMe(t);
      const name = me.display_name ?? me.email.split('@')[0];
      setDisplayName(name);
      localStorage.setItem(NAME_KEY, name);
    } catch {
      // non-critical
    }
    setScreen('dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(NAME_KEY);
    setToken(null);
    setDisplayName('');
    setSessionId(null);
    setScreen('login');
  };

  const screenLabel: Record<Screen, string | null> = {
    login:     null,
    dashboard: null,
    quiz:      'Quiz Session',
    results:   'Results',
    review:    'Review Mode',
  };

  return (
    <div className="min-h-screen bg-dark-bg text-gray-100 pb-20">

      {/* ── Navbar ── */}
      <nav className="nav-bar border-b border-dark-border sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">

          {/* Logo */}
          <button
            type="button"
            onClick={() => token && setScreen('dashboard')}
            className="flex items-center gap-2.5 group"
          >
            <div className="w-7 h-7 rounded-lg bg-brand-500 flex items-center justify-center text-white font-bold text-sm shadow-md shadow-brand-500/30">
              A
            </div>
            <span className="font-bold text-base tracking-tight text-white uppercase">Architekt</span>
          </button>

          {/* Breadcrumb */}
          {screenLabel[screen] && (
            <span className="text-xs font-semibold uppercase tracking-widest text-gray-500 hidden sm:block">
              {screenLabel[screen]}
            </span>
          )}

          {/* Right side */}
          {token ? (
            <div className="flex items-center gap-3">
              {displayName && (
                <div className="hidden sm:flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-brand-500/20 border border-brand-500/30 flex items-center justify-center text-brand-400 text-xs font-bold">
                    {displayName[0].toUpperCase()}
                  </div>
                  <span className="text-sm text-gray-400">{displayName}</span>
                </div>
              )}
              <button
                type="button"
                onClick={handleLogout}
                className="text-xs font-semibold uppercase tracking-wide text-gray-500 hover:text-gray-200 transition-colors"
              >
                Logout
              </button>
            </div>
          ) : (
            <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">v1.0</span>
          )}
        </div>
      </nav>

      {/* ── Screens ── */}
      <main className="max-w-5xl mx-auto px-4">
        {screen === 'login' && (
          <LoginStart onSuccess={handleAuthSuccess} />
        )}
        {screen === 'dashboard' && token && (
          <Dashboard
            token={token}
            displayName={displayName}
            onStartQuiz={(id) => { setSessionId(id); setScreen('quiz'); }}
            onStartReview={() => setScreen('review')}
          />
        )}
        {screen === 'quiz' && token && sessionId && (
          <QuizSession
            token={token}
            sessionId={sessionId}
            onCompleted={() => setScreen('results')}
            onExit={() => setScreen('dashboard')}
          />
        )}
        {screen === 'results' && token && sessionId && (
          <ResultsScreen
            token={token}
            sessionId={sessionId}
            onBackToDashboard={() => setScreen('dashboard')}
          />
        )}
        {screen === 'review' && token && (
          <ReviewScreen token={token} onDone={() => setScreen('dashboard')} />
        )}
      </main>

      {/* ── Footer ── */}
      <footer className="footer-bar fixed bottom-0 left-0 right-0 border-t border-dark-border h-10 flex items-center justify-center z-50">
        <span className="text-[10px] text-gray-600 uppercase tracking-widest">
          Deterministic Learning Engine &bull; Architekt v1.0
        </span>
      </footer>
    </div>
  );
}

export default App;
