import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { Scale, Mail, Lock, ArrowRight } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

export default function LoginPage() {
  const { t } = useTranslation();
  const { login, isLoading } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('priya@karnataka.gov.in');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch {
      setError('Invalid credentials. Please try again.');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0f172a] p-4">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-blue-500/5 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 h-80 w-80 rounded-full bg-purple-500/5 blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="relative w-full max-w-md"
      >
        <div className="glass-card p-8">
          {/* Logo */}
          <div className="mb-8 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-blue-700 shadow-lg shadow-blue-500/25">
              <Scale size={28} className="text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white">{t('auth.loginTitle')}</h1>
            <p className="mt-1 text-sm text-slate-400">{t('auth.loginSubtitle')}</p>
          </div>

          {error && (
            <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-300">{t('auth.email')}</label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800/50 py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-colors"
                  placeholder="email@karnataka.gov.in"
                  required
                />
              </div>
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-300">{t('auth.password')}</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800/50 py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-colors"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            {/* Role hint */}
            <div className="rounded-lg bg-slate-800/30 border border-slate-700/50 p-3">
              <p className="text-xs text-slate-500 mb-2">Demo roles (use any email):</p>
              <div className="grid grid-cols-2 gap-1">
                {(['reviewer', 'dept_officer', 'dept_head', 'legal_advisor'] as const).map(role => (
                  <span key={role} className="text-[10px] text-slate-400 bg-slate-800/50 rounded px-2 py-1">
                    {role.replace('_', ' ')}
                  </span>
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-blue-600 to-blue-500 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-500/25 hover:from-blue-500 hover:to-blue-400 disabled:opacity-50 transition-all"
            >
              {isLoading ? 'Signing in...' : t('auth.login')}
              {!isLoading && <ArrowRight size={16} />}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            {t('auth.noAccount')}{' '}
            <Link to="/register" className="text-blue-400 hover:text-blue-300 transition-colors">
              {t('auth.register')}
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
