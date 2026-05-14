import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'motion/react';
import { useAuth } from './context/AuthContext';
import { Department, fetchDepartments } from './api/client';
import karnatakaLogo from './karnataka_govt_logo.png';

const ROLE_OPTIONS = [
  { value: 'head_legal_cell', label: 'Head of Legal Cell', desc: 'Verifies & approves AI extractions (department-scoped)' },
  { value: 'nodal_officer', label: 'Nodal Officer', desc: 'Monitors statutory deadlines (department-scoped)' },
  { value: 'lco', label: 'Litigation Conducting Officer', desc: 'Executes court directions (case-scoped)' },
  { value: 'central_law', label: 'Central Law Department', desc: 'State-wide oversight across all 48 departments' },
  { value: 'state_monitoring', label: 'State Monitoring Committee', desc: 'Audit & compliance reporting (global)' },
];

const FEATURES = [
  { icon: 'auto_awesome', title: 'Intelligent Extraction', body: 'Multi-agent LLM pipeline reads judgment PDFs and extracts case metadata, directives, parties, and timelines.' },
  { icon: 'fact_check', title: 'Actionable Plans', body: 'AI-generated compliance and appeal recommendations with statutory deadlines per the Limitation Act.' },
  { icon: 'verified_user', title: 'Human-in-the-loop', body: 'Mandatory HLC verification ensures only accurate, approved data reaches the department dashboard.' },
];

export default function RegisterPage() {
  const { register, isLoading } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: '',
    password: '',
    confirm_password: '',
    role: 'head_legal_cell',
    department_code: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [departments, setDepartments] = useState<Department[]>([]);

  useEffect(() => {
    fetchDepartments().then(setDepartments).catch(err => console.error('Dept list fetch failed:', err));
  }, []);

  const isGlobalRole = form.role === 'central_law' || form.role === 'state_monitoring';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (form.password !== form.confirm_password) {
      setError('Passwords do not match');
      return;
    }
    if (!isGlobalRole && !form.department_code) {
      setError('Please pick a department (required for department-scoped roles).');
      return;
    }
    try {
      await register({
        username: form.username,
        email: form.username.includes('@') ? form.username : `${form.username}@nyayadrishti.in`,
        password: form.password,
        role: form.role,
        department_code: isGlobalRole ? '' : form.department_code,
      });
      navigate('/login');
    } catch (err: any) {
      setError(err?.message || 'Registration failed. Please try again.');
    }
  };

  const upd = (field: string, value: string) => setForm(p => ({ ...p, [field]: value }));

  const inputCls = 'w-full bg-surface-container-highest/40 border-b-2 border-outline-variant/30 focus:border-primary-blue/70 focus:bg-surface-container-highest/60 outline-none rounded-t-lg pl-10 pr-10 py-2.5 text-sm text-on-surface transition-all placeholder:text-on-surface-variant/50';

  return (
    <div className="min-h-screen w-full flex flex-col lg:flex-row bg-surface-dim text-on-surface relative">
      {/* Background dot grid (whole page) */}
      <div
        className="absolute inset-0 opacity-[0.06] pointer-events-none z-0"
        style={{
          backgroundImage: 'radial-gradient(currentColor 1px, transparent 1px)',
          backgroundSize: '24px 24px',
        }}
      />

      {/* ─── Left panel: marketing (hidden on small) ─── */}
      <aside className="hidden lg:flex lg:w-1/2 relative z-10 px-10 xl:px-16 py-12 flex-col justify-center overflow-hidden bg-surface">
        {/* Decorative gradient + extra dot column */}
        <div className="absolute inset-0 pointer-events-none">
          <div
            className="absolute inset-0"
            style={{ background: 'radial-gradient(circle at 100% 50%, rgba(173,198,255,0.10) 0%, transparent 60%)' }}
          />
          <div
            className="absolute left-0 top-0 bottom-0 w-60 opacity-25"
            style={{
              backgroundImage: 'radial-gradient(rgba(173,198,255,0.5) 1.5px, transparent 1.5px)',
              backgroundSize: '32px 32px',
              maskImage: 'linear-gradient(to right, black, transparent)',
              WebkitMaskImage: 'linear-gradient(to right, black, transparent)',
            }}
          />
        </div>

        <motion.div
          initial={{ opacity: 0, x: -24 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="relative z-10 max-w-xl"
        >
          <div className="flex items-center gap-4 mb-8">
            <img
              src={karnatakaLogo}
              alt="Government of Karnataka"
              className="w-14 h-14 rounded-full ring-1 ring-outline-variant/40 shadow-lg bg-white/5 p-1"
            />
            <div>
              <h1 className="text-4xl xl:text-5xl font-bold text-primary-blue tracking-tighter leading-none">
                NyayaDrishti
              </h1>
              <p className="text-[10px] uppercase font-bold tracking-[0.2em] text-on-surface-variant opacity-60 mt-1">
                Govt. of Karnataka · CCMS
              </p>
            </div>
          </div>

          <h2 className="text-2xl xl:text-3xl font-semibold text-on-surface mt-6 leading-tight">
            Integrated Legal Intelligence for the State Secretariat
          </h2>
          <p className="text-base text-on-surface-variant leading-relaxed mt-4 max-w-md">
            AI reads court judgments, drafts actionable compliance plans, and routes them to the
            responsible department — with mandatory human verification at every step.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="relative z-10 mt-12 xl:mt-16 grid grid-cols-1 gap-3 max-w-xl"
        >
          {FEATURES.map(f => (
            <div
              key={f.title}
              className="flex items-start gap-4 p-4 rounded-2xl bg-surface-container/50 backdrop-blur-sm border border-outline-variant/20"
            >
              <div className="shrink-0 w-10 h-10 rounded-xl bg-primary-blue/10 border border-primary-blue/20 flex items-center justify-center text-primary-blue">
                <span className="material-symbols-outlined text-xl">{f.icon}</span>
              </div>
              <div className="min-w-0">
                <h4 className="text-sm font-bold text-on-surface">{f.title}</h4>
                <p className="text-xs text-on-surface-variant opacity-80 leading-relaxed mt-0.5">{f.body}</p>
              </div>
            </div>
          ))}
        </motion.div>
      </aside>

      {/* ─── Right panel: registration form ─── */}
      <main className="relative z-10 w-full lg:w-1/2 flex items-start justify-center px-4 sm:px-6 py-6 sm:py-8 lg:py-10 overflow-y-auto min-h-screen">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md glass-card p-5 sm:p-6 relative my-auto"
        >
          <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-transparent via-primary-blue/60 to-transparent" />

          {/* Mobile-only brand (shown above the card on <lg) */}
          <div className="flex lg:hidden items-center gap-3 mb-5">
            <img
              src={karnatakaLogo}
              alt="Government of Karnataka"
              className="w-10 h-10 rounded-full ring-1 ring-outline-variant/40 bg-white/5 p-0.5 shrink-0"
            />
            <div className="leading-tight">
              <p className="text-lg font-bold text-primary-blue tracking-tight">NyayaDrishti</p>
              <p className="text-[9px] uppercase tracking-[0.18em] font-bold text-on-surface-variant opacity-60">
                Govt. of Karnataka · CCMS
              </p>
            </div>
          </div>

          {/* Card header */}
          <div className="flex flex-col items-center text-center gap-2 mb-4">
            <div className="w-11 h-11 rounded-full bg-primary-blue/10 border border-primary-blue/20 flex items-center justify-center">
              <span className="material-symbols-outlined text-xl text-primary-blue">person_add</span>
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-on-surface tracking-tight">Create Account</h2>
              <p className="text-xs text-on-surface-variant opacity-80 mt-0.5">
                Register a new node on the CCMS network.
              </p>
            </div>
          </div>

          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-4 px-3 py-2 rounded-lg bg-error-red/10 border border-error-red/30 text-error-red text-xs font-semibold"
              >
                {error}
              </motion.div>
            )}
          </AnimatePresence>

          <form onSubmit={handleSubmit} className="space-y-3">
            {/* User ID */}
            <Field
              id="username"
              label="User ID"
              placeholder="your.name or email"
              value={form.username}
              onChange={v => upd('username', v)}
              icon="person"
            />

            {/* Password (with toggle) */}
            <div className="space-y-1">
              <label htmlFor="password" className="block text-[10px] font-bold uppercase tracking-wider text-on-surface-variant ml-0.5">
                Password
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-lg pointer-events-none">
                  lock
                </span>
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={form.password}
                  onChange={e => upd('password', e.target.value)}
                  placeholder="Choose a secure password"
                  className={inputCls}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(s => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  <span className="material-symbols-outlined text-lg">
                    {showPassword ? 'visibility_off' : 'visibility'}
                  </span>
                </button>
              </div>
            </div>

            {/* Confirm Password (with toggle) */}
            <div className="space-y-1">
              <label htmlFor="confirm_password" className="block text-[10px] font-bold uppercase tracking-wider text-on-surface-variant ml-0.5">
                Confirm Password
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-lg pointer-events-none">
                  shield
                </span>
                <input
                  id="confirm_password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  required
                  value={form.confirm_password}
                  onChange={e => upd('confirm_password', e.target.value)}
                  placeholder="Re-enter password"
                  className={inputCls}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(s => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface transition-colors"
                  aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                >
                  <span className="material-symbols-outlined text-lg">
                    {showConfirmPassword ? 'visibility_off' : 'visibility'}
                  </span>
                </button>
              </div>
            </div>

            {/* Role */}
            <div className="space-y-1">
              <SelectField
                id="role"
                label="Role"
                value={form.role}
                onChange={v => upd('role', v)}
                icon="badge"
              >
                {ROLE_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value} className="bg-surface-dim text-on-surface">
                    {opt.label}
                  </option>
                ))}
              </SelectField>
              <p className="text-[10px] text-on-surface-variant opacity-70 ml-1">
                {ROLE_OPTIONS.find(o => o.value === form.role)?.desc}
              </p>
            </div>

            {/* Department (only for dept-scoped roles) */}
            {!isGlobalRole && (
              <SelectField
                id="department_code"
                label="Department (Karnataka Secretariat)"
                value={form.department_code}
                onChange={v => upd('department_code', v)}
                icon="account_balance"
              >
                <option value="" disabled className="bg-surface-dim">Select your department…</option>
                {departments.map(d => (
                  <option key={d.code} value={d.code} className="bg-surface-dim text-on-surface">
                    {d.name}
                  </option>
                ))}
              </SelectField>
            )}
            {isGlobalRole && (
              <p className="text-[10px] text-on-surface-variant opacity-70 italic text-center">
                Central / monitoring roles have global access — no single department.
              </p>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-1 px-4 py-2.5 rounded-lg bg-primary-blue text-on-primary-blue font-bold text-xs uppercase tracking-widest shadow-lg shadow-primary-blue/20 hover:bg-primary-blue/90 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all"
            >
              {isLoading ? (
                <>
                  <span className="material-symbols-outlined text-base animate-spin">progress_activity</span>
                  Creating account…
                </>
              ) : (
                <>
                  Create Account
                  <span className="material-symbols-outlined text-base">arrow_forward</span>
                </>
              )}
            </button>

            <p className="text-center text-xs text-on-surface-variant pb-1">
              Already have an account?{' '}
              <Link to="/login" className="text-primary-blue font-semibold hover:underline">
                Sign in
              </Link>
            </p>
          </form>
        </motion.div>
      </main>
    </div>
  );
}

// ─── Field primitives ───────────────────────────────────────────────────────

const Field: React.FC<{
  id: string;
  label: string;
  placeholder: string;
  value: string;
  onChange: (v: string) => void;
  icon: string;
  type?: string;
}> = ({ id, label, placeholder, value, onChange, icon, type = 'text' }) => (
  <div className="space-y-1">
    <label htmlFor={id} className="block text-[10px] font-bold uppercase tracking-wider text-on-surface-variant ml-0.5">
      {label}
    </label>
    <div className="relative">
      <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-lg pointer-events-none">
        {icon}
      </span>
      <input
        id={id}
        type={type}
        required
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-surface-container-highest/40 border-b-2 border-outline-variant/30 focus:border-primary-blue/70 focus:bg-surface-container-highest/60 outline-none rounded-t-lg pl-10 pr-3 py-2.5 text-sm text-on-surface transition-all placeholder:text-on-surface-variant/50"
      />
    </div>
  </div>
);

const SelectField: React.FC<{
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  icon: string;
  children: React.ReactNode;
}> = ({ id, label, value, onChange, icon, children }) => (
  <div className="space-y-1">
    <label htmlFor={id} className="block text-[10px] font-bold uppercase tracking-wider text-on-surface-variant ml-0.5">
      {label}
    </label>
    <div className="relative">
      <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-lg pointer-events-none">
        {icon}
      </span>
      <select
        id={id}
        required
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full appearance-none bg-surface-container-highest/40 border-b-2 border-outline-variant/30 focus:border-primary-blue/70 focus:bg-surface-container-highest/60 outline-none rounded-t-lg pl-10 pr-10 py-2.5 text-sm text-on-surface cursor-pointer transition-all"
      >
        {children}
      </select>
      <span className="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-lg pointer-events-none">
        expand_more
      </span>
    </div>
  </div>
);
