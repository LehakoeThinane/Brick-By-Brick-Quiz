import { useState } from 'react';
import { login, register } from '../api/client';

type Props = {
  onSuccess: (token: string) => void;
};

type Mode = 'login' | 'register';

export function LoginStart({ onSuccess }: Props) {
  const [mode,         setMode]         = useState<Mode>('login');
  const [email,        setEmail]        = useState('');
  const [password,     setPassword]     = useState('');
  const [displayName,  setDisplayName]  = useState('');
  const [error,        setError]        = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submit = async () => {
    setError(null);
    setIsSubmitting(true);
    try {
      if (mode === 'login') {
        const token = await login({ email, password });
        onSuccess(token);
      } else {
        const token = await register({ email, password, display_name: displayName || undefined });
        onSuccess(token);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && email && password) submit();
  };

  const switchMode = (m: Mode) => { setMode(m); setError(null); };

  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm animate-scale-in">

        {/* Brand mark */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-brand-500 flex items-center justify-center mb-4 shadow-lg shadow-brand-500/30">
            <span className="text-white font-bold text-2xl">A</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">ARCHITEKT</h1>
          <p className="text-sm text-gray-500 mt-1">Adaptive Technical Mastery</p>
        </div>

        {/* Card */}
        <div className="glass-panel p-6">

          {/* Mode toggle */}
          <div className="mode-toggle flex rounded-xl overflow-hidden border border-dark-border mb-6">
            {(['login', 'register'] as Mode[]).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => switchMode(m)}
                className={`flex-1 py-2 text-sm font-semibold transition-all duration-150 ${
                  mode === m
                    ? 'bg-brand-500 text-white shadow-sm'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                {m === 'login' ? 'Log in' : 'Register'}
              </button>
            ))}
          </div>

          <div className="space-y-4">
            <div>
              <label className="section-label block mb-1.5">Email</label>
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={handleKey}
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                className="form-input"
              />
            </div>

            <div>
              <label className="section-label block mb-1.5">Password</label>
              <input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={handleKey}
                type="password"
                autoComplete="password"
                placeholder="Minimum 8 characters"
                className="form-input"
              />
            </div>

            {mode === 'register' && (
              <div className="animate-slide-up">
                <label className="section-label block mb-1.5">
                  Display Name{' '}
                  <span className="normal-case text-gray-600">(optional)</span>
                </label>
                <input
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  onKeyDown={handleKey}
                  type="text"
                  autoComplete="name"
                  placeholder="e.g. Lehakoe"
                  className="form-input"
                />
              </div>
            )}
          </div>

          {error && (
            <div className="mt-4 px-3.5 py-2.5 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-400 animate-fade-in">
              {error}
            </div>
          )}

          <button
            type="button"
            onClick={submit}
            disabled={isSubmitting || !email || !password}
            className="btn-primary w-full mt-5"
          >
            {isSubmitting
              ? 'Please wait…'
              : mode === 'login' ? 'Log in' : 'Create account'}
          </button>
        </div>

        <p className="text-center text-xs text-gray-600 mt-6">
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <button
            type="button"
            onClick={() => switchMode(mode === 'login' ? 'register' : 'login')}
            className="text-brand-500 hover:text-brand-400 font-medium transition-colors"
          >
            {mode === 'login' ? 'Register' : 'Log in'}
          </button>
        </p>
      </div>
    </div>
  );
}
