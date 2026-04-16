import { useState } from 'react';
import { login, register } from '../api/client';

type Props = {
  onSuccess: (token: string) => void;
};

type Mode = 'login' | 'register';

export function LoginStart({ onSuccess }: Props) {
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submit = async () => {
    setError(null);
    setIsSubmitting(true);
    try {
      if (mode === 'login') {
        const token = await login({ email, password });
        onSuccess(token);
      } else {
        const token = await register({
          email,
          password,
          display_name: displayName || undefined,
        });
        onSuccess(token);
      }
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Login failed';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-12 px-4 pb-24 animate-fade-in">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-white tracking-tight">ARCHITEKT</h1>
        <p className="text-gray-400 mt-2">Adaptive Technical Mastery Quiz Platform</p>
      </header>

      <div className="glass-panel p-6 border border-dark-border">
        <div className="flex gap-3 mb-5">
          <button
            onClick={() => setMode('login')}
            className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
              mode === 'login' ? 'bg-brand-500/20 text-brand-500' : 'bg-dark-surface/50 text-gray-300 hover:text-white'
            }`}
          >
            Login
          </button>
          <button
            onClick={() => setMode('register')}
            className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
              mode === 'register' ? 'bg-brand-500/20 text-brand-500' : 'bg-dark-surface/50 text-gray-300 hover:text-white'
            }`}
          >
            Register
          </button>
        </div>

        <label className="block text-sm text-gray-300 mb-2">Email</label>
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full mb-4 px-3 py-2 rounded-md bg-dark-surface/50 border border-dark-border outline-none focus:border-brand-500"
          type="email"
          placeholder="you@example.com"
        />

        <label className="block text-sm text-gray-300 mb-2">Password</label>
        <input
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full mb-4 px-3 py-2 rounded-md bg-dark-surface/50 border border-dark-border outline-none focus:border-brand-500"
          type="password"
          placeholder="Minimum 8 characters"
        />

        {mode === 'register' && (
          <>
            <label className="block text-sm text-gray-300 mb-2">Display Name (optional)</label>
            <input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full mb-4 px-3 py-2 rounded-md bg-dark-surface/50 border border-dark-border outline-none focus:border-brand-500"
              type="text"
              placeholder="e.g. Stanley"
            />
          </>
        )}

        {error && <div className="text-sm text-red-300 mb-4">{error}</div>}

        <button
          onClick={submit}
          disabled={isSubmitting || !email || !password}
          className="btn-primary w-full disabled:opacity-50"
        >
          {isSubmitting ? 'Please wait...' : mode === 'login' ? 'Login' : 'Create account'}
        </button>
      </div>
    </div>
  );
}

