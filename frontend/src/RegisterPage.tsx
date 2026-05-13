import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'motion/react';
import { useAuth } from './context/AuthContext';
import { Gavel, User, Lock, Building, ArrowRight, ShieldCheck, Eye, EyeOff, Brain, TrendingUp, Calendar, Clock } from 'lucide-react';

const S = {
  page: {
    height: '100vh',
    width: '100%',
    display: 'flex' as const,
    backgroundColor: '#0b0e14', // bg-background (surface-container-lowest)
    fontFamily: "'Inter', system-ui, sans-serif",
    overflow: 'hidden' as const,
    position: 'relative' as const,
  },
  leftCol: {
    width: '50%',
    display: 'flex' as const,
    flexDirection: 'column' as const,
    justifyContent: 'center' as const,
    padding: '3rem',
    position: 'relative' as const,
    zIndex: 1,
    backgroundColor: '#10131a', // bg-surface-dim
  },
  logoRow: {
    display: 'flex' as const,
    alignItems: 'center' as const,
    gap: '0.75rem',
    marginBottom: '1.5rem',
  },
  appName: {
    fontSize: '3rem', fontWeight: 700,
    color: '#3b82f6', letterSpacing: '-0.02em', lineHeight: 1.1,
  },
  tagline: {
    fontSize: '1.875rem', fontWeight: 300,
    color: '#e1e2ec', marginBottom: '1rem', lineHeight: 1.3,
  },
  desc: {
    fontSize: '1.125rem', color: '#c2c6d6',
    lineHeight: 1.6, fontWeight: 400, maxWidth: '30rem',
  },
  rightCol: {
    flex: 1,
    display: 'flex' as const,
    alignItems: 'center' as const,
    justifyContent: 'center' as const,
    padding: '1rem',
    position: 'relative' as const,
    zIndex: 1,
    overflowY: 'auto' as const,
  },
  card: {
    width: '100%',
    maxWidth: '480px',
    backgroundColor: 'rgba(29,32,39,0.7)', // surface-container/70
    backdropFilter: 'blur(24px)',
    WebkitBackdropFilter: 'blur(24px)',
    border: '1px solid rgba(66,71,84,0.3)', // outline-variant/30
    borderRadius: '8px',
    boxShadow: '0 20px 40px -10px rgba(0,0,0,0.5)',
    padding: '2rem',
    position: 'relative' as const,
    overflow: 'hidden' as const,
    display: 'flex' as const,
    flexDirection: 'column' as const,
    gap: '1.5rem',
  },
  cardHeading: {
    fontSize: '2rem', fontWeight: 700, color: '#e1e2ec',
    textAlign: 'center' as const, marginBottom: '0.25rem', letterSpacing: '-0.02em',
  },
  cardSubheading: {
    fontSize: '1rem', color: '#c2c6d6',
    textAlign: 'center' as const, marginBottom: '0.5rem',
  },
  fieldLabel: {
    display: 'block' as const, fontSize: '0.75rem', fontWeight: 700,
    color: '#c2c6d6', textTransform: 'uppercase' as const,
    letterSpacing: '0.05em', marginBottom: '0.25rem', marginLeft: '0.25rem',
  },
  inputWrap: { position: 'relative' as const },
  iconWrap: {
    position: 'absolute' as const, left: '0.75rem', top: '50%',
    transform: 'translateY(-50%)', color: '#8c909f', // outline-variant
    display: 'flex' as const, alignItems: 'center' as const,
    pointerEvents: 'none' as const,
  },
  input: {
    width: '100%', boxSizing: 'border-box' as const,
    backgroundColor: 'rgba(50,53,60,0.4)', // surface-variant/40
    border: 'none',
    borderBottom: '2px solid rgba(140,144,159,0.3)', // border-b-outline/30
    borderRadius: '8px 8px 0 0',
    padding: '0.75rem 1rem 0.75rem 2.5rem',
    color: '#e1e2ec', fontSize: '1rem', fontWeight: 400,
    outline: 'none', transition: 'all 0.2s', fontFamily: 'inherit',
  },
  submitBtn: {
    width: '100%',
    backgroundColor: '#3b82f6', color: '#002e6a', // primary bg, on-primary text
    fontWeight: 700, fontSize: '0.875rem',
    padding: '0.75rem 1.5rem',
    borderRadius: '8px', border: '1px solid transparent', cursor: 'pointer',
    display: 'flex' as const, alignItems: 'center' as const,
    justifyContent: 'center' as const, gap: '0.5rem',
    letterSpacing: '0.05em', textTransform: 'uppercase' as const,
    boxShadow: '0 0 15px rgba(59,130,246,0.25)',
    transition: 'all 0.2s', fontFamily: 'inherit',
    marginTop: '0.5rem',
  },
  footer: {
    textAlign: 'center' as const, fontSize: '0.875rem',
  },
};

const focusOn  = (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement>) => { 
  e.currentTarget.style.borderColor = '#3b82f6';
  e.currentTarget.style.backgroundColor = 'rgba(50,53,60,0.6)';
};
const focusOff = (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement>) => { 
  e.currentTarget.style.borderColor = 'rgba(140,144,159,0.3)';
  e.currentTarget.style.backgroundColor = 'rgba(50,53,60,0.4)';
};

export default function RegisterPage() {
  const { register, isLoading } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: '', password: '', confirm_password: '', department: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (form.password !== form.confirm_password) { setError('Passwords do not match'); return; }
    try {
      await register({
        username: form.username,
        email: form.username.includes('@') ? form.username : `${form.username}@nyayadrishti.in`,
        password: form.password,
        role: 'reviewer', // default role
        department: form.department || 'legal',
      });
      navigate('/login');
    } catch (err: any) {
      setError(err?.message || 'Registration failed. Please try again.');
    }
  };

  const upd = (field: string, value: string) => setForm(p => ({ ...p, [field]: value }));

  return (
    <div style={S.page}>
      {/* Dot Grid Background over everything */}
      <div style={{ position: 'absolute', inset: 0, opacity: 0.1, backgroundImage: 'radial-gradient(#ffffff 1px, transparent 1px)', backgroundSize: '24px 24px', pointerEvents: 'none', zIndex: 0 }} />

      {/* Left column */}
      <div className="hidden lg:flex" style={S.leftCol}>
        <div style={{ position: 'absolute', inset: 0, zIndex: 0, overflow: 'hidden', pointerEvents: 'none' }}>
          {/* Deep Dark Gradient */}
          <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(circle at 100% 50%, rgba(59,130,246,0.15) 0%, rgba(10,12,18,1) 100%)' }} />
          
          {/* Left Side Dot Grid - Matching Screenshot */}
          <div style={{ 
            position: 'absolute', 
            top: 0, 
            left: 0, 
            bottom: 0, 
            width: '240px', 
            opacity: 0.2, 
            backgroundImage: 'radial-gradient(rgba(59,130,246,0.5) 1.5px, transparent 1.5px)', 
            backgroundSize: '32px 32px',
            maskImage: 'linear-gradient(to right, black, transparent)'
          }} />

          {/* Faint Document Background */}
          <img alt="" src="https://images.unsplash.com/photo-1589829545856-d10d557cf95f?q=80&w=2070&auto=format&fit=crop" 
            style={{ position: 'absolute', top: 0, right: 0, width: '80%', height: '100%', objectFit: 'cover', opacity: 0.03, mixBlendMode: 'luminosity', filter: 'blur(4px)' }} />

          {/* Glowing Shield/Lock with Orbits Graphic - Right side of left panel */}
          <div style={{ position: 'absolute', top: '50%', right: '-80px', transform: 'translateY(-50%)', width: '400px', height: '400px' }}>
             {/* Orbits */}
             <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: '1px solid rgba(59,130,246,0.1)', transform: 'scale(1.2)' }} />
             <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: '1px solid rgba(59,130,246,0.05)', transform: 'scale(1.5) rotate(15deg)' }} />
             
             {/* Glowing Shield Icon */}
             <div style={{ 
               position: 'absolute', 
               top: '50%', 
               left: '50%', 
               transform: 'translate(-50%, -50%)', 
               width: '80px', 
               height: '80px', 
               backgroundColor: 'rgba(59,130,246,0.1)', 
               borderRadius: '20px', 
               display: 'flex', 
               alignItems: 'center', 
               justifyContent: 'center',
               border: '1px solid rgba(59,130,246,0.3)',
               boxShadow: '0 0 40px rgba(59,130,246,0.2)'
             }}>
                <Lock size={32} color="#3b82f6" />
                <div style={{ position: 'absolute', top: '-10px', right: '20px', width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#3b82f6', boxShadow: '0 0 10px #3b82f6' }} />
                <div style={{ position: 'absolute', bottom: '20px', left: '-10px', width: '4px', height: '4px', borderRadius: '50%', backgroundColor: '#3b82f6', opacity: 0.6 }} />
             </div>
          </div>
        </div>

        <div style={{ position: 'relative', zIndex: 1, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <motion.div initial={{ opacity: 0, x: -28 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.8 }} style={{ maxWidth: '36rem' }}>
            <div style={S.logoRow}>
              <Gavel style={{ width: '52px', height: '52px', color: '#3b82f6' }} />
              <h1 style={{ ...S.appName, fontSize: '3.5rem', fontWeight: 800 }}>NyayaDrishti</h1>
            </div>
            <h2 style={{ ...S.tagline, fontSize: '2rem', marginTop: '0.5rem' }}>Integrated Legal Intelligence</h2>
            <p style={{ ...S.desc, fontSize: '1.125rem', lineHeight: 1.6, maxWidth: '90%', marginTop: '1.5rem', color: '#c2c6d6' }}>
              AI-powered system that reads court judgments, generates actionable plans, and ensures human-verified accuracy for government use.
            </p>
          </motion.div>

          {/* Feature Highlight Boxes */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.8 }}
            style={{ display: 'flex', gap: '1.5rem', marginTop: '8rem' }}
          >
            <div style={{ flex: 1, backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', padding: '1.5rem', borderRadius: '16px', display: 'flex', alignItems: 'flex-start', gap: '1.25rem' }}>
              <div style={{ padding: '0.85rem', backgroundColor: 'rgba(59,130,246,0.1)', borderRadius: '12px', color: '#3b82f6', border: '1px solid rgba(59,130,246,0.2)' }}>
                <ShieldCheck size={24} />
              </div>
              <div style={{ flex: 1 }}>
                <h4 style={{ color: '#e1e2ec', fontSize: '15px', fontWeight: 700, marginBottom: '6px' }}>Intelligent Extraction</h4>
                <p style={{ color: '#c2c6d6', fontSize: '12px', lineHeight: 1.5, opacity: 0.8 }}>Extract case details, directions, parties, timelines, and more from judgment PDFs.</p>
              </div>
            </div>

            <div style={{ flex: 1, backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', padding: '1.5rem', borderRadius: '16px', display: 'flex', alignItems: 'flex-start', gap: '1.25rem' }}>
              <div style={{ padding: '0.85rem', backgroundColor: 'rgba(59,130,246,0.1)', borderRadius: '12px', color: '#3b82f6', border: '1px solid rgba(59,130,246,0.2)' }}>
                <Calendar size={24} />
              </div>
              <div style={{ flex: 1 }}>
                <h4 style={{ color: '#e1e2ec', fontSize: '15px', fontWeight: 700, marginBottom: '6px' }}>Actionable Plans</h4>
                <p style={{ color: '#c2c6d6', fontSize: '12px', lineHeight: 1.5, opacity: 0.8 }}>Generate compliance needs, appeal considerations, responsible departments, and timelines.</p>
              </div>
            </div>

            <div style={{ flex: 1, backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', padding: '1.5rem', borderRadius: '16px', display: 'flex', alignItems: 'flex-start', gap: '1.25rem' }}>
              <div style={{ padding: '0.85rem', backgroundColor: 'rgba(59,130,246,0.1)', borderRadius: '12px', color: '#3b82f6', border: '1px solid rgba(59,130,246,0.2)' }}>
                <ShieldCheck size={24} />
              </div>
              <div style={{ flex: 1 }}>
                <h4 style={{ color: '#e1e2ec', fontSize: '15px', fontWeight: 700, marginBottom: '6px' }}>Verified & Trusted</h4>
                <p style={{ color: '#c2c6d6', fontSize: '12px', lineHeight: 1.5, opacity: 0.8 }}>Human-in-the-loop verification ensures only accurate, approved data reaches the dashboard.</p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Right column */}
      <main style={S.rightCol}>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} style={S.card}>
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '4px', background: 'linear-gradient(90deg, transparent, rgba(59,130,246,0.5), transparent)' }} />
          
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '50%', backgroundColor: 'rgba(59,130,246,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(59,130,246,0.2)' }}>
              <User size={28} color="#3b82f6" />
            </div>
            <div style={{ textAlign: 'center' }}>
              <h2 style={S.cardHeading}>Create Account</h2>
              <p style={S.cardSubheading}>Initialize your secure legal intelligence node.</p>
            </div>
          </div>

          <AnimatePresence>
            {error && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                style={{ backgroundColor: 'rgba(255,180,171,0.1)', border: '1px solid rgba(255,180,171,0.2)', padding: '0.75rem', borderRadius: '8px', color: '#ffb4ab', fontSize: '12px', fontWeight: 600 }}>
                {error}
              </motion.div>
            )}
          </AnimatePresence>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <Field id="username" label="User ID" placeholder="Enter your credentials ID" value={form.username} onChange={v => upd('username', v)} icon={<User style={{ width: '18px', height: '18px' }} />} />
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <label style={S.fieldLabel}>Password</label>
              <div style={S.inputWrap}>
                <div style={S.iconWrap}><Lock style={{ width: '18px', height: '18px' }} /></div>
                <input id="password" type={showPassword ? 'text' : 'password'} placeholder="Create secure password"
                  value={form.password} onChange={e => upd('password', e.target.value)} required
                  style={{ ...S.input, paddingRight: '2.5rem' }} onFocus={focusOn} onBlur={focusOff} />
                <button type="button" onClick={() => setShowPassword(!showPassword)}
                  style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#8c909f' }}>
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <Field id="confirm_password" label="Confirm Password" type="password" placeholder="Verify password"
              value={form.confirm_password} onChange={v => upd('confirm_password', v)}
              icon={<ShieldCheck style={{ width: '18px', height: '18px' }} />} />

            <SelectField id="department" label="Department" value={form.department} onChange={v => upd('department', v)} icon={<Building style={{ width: '18px', height: '18px' }} />}>
              <option value="" disabled style={{ backgroundColor: '#10131a' }}>Select Designation...</option>
              <option value="legal">Legal</option>
              <option value="finance">Finance</option>
              <option value="executive">Executive</option>
              <option value="external">External Counsel</option>
            </SelectField>

            <button type="submit" disabled={isLoading}
              style={{ ...S.submitBtn, opacity: isLoading ? 0.6 : 1 }}
              onMouseEnter={e => !isLoading && (e.currentTarget.style.backgroundColor = '#2563eb')}
              onMouseLeave={e => (e.currentTarget.style.backgroundColor = '#3b82f6')}>
              {isLoading ? 'Creating account...' : (<>CREATE ACCOUNT <ArrowRight size={18} /></>)}
            </button>

            <div style={S.footer}>
              <Link to="/login" style={{ color: '#3b82f6', fontWeight: 600, textDecoration: 'none' }}
                onMouseEnter={e => (e.currentTarget.style.textDecoration = 'underline')}
                onMouseLeave={e => (e.currentTarget.style.textDecoration = 'none')}>
                Already have an account? Login
              </Link>
            </div>
          </form>
        </motion.div>
      </main>
    </div>
  );
}

const Field = ({ id, label, type = 'text', placeholder, value, onChange, icon, pr }: {
  id: string; label: string; type?: string; placeholder: string;
  value: string; onChange: (v: string) => void; icon: React.ReactNode; pr?: boolean;
}) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
    <label style={S.fieldLabel} htmlFor={id}>{label}</label>
    <div style={S.inputWrap}>
      <div style={S.iconWrap}>{icon}</div>
      <input id={id} type={type} placeholder={placeholder} value={value}
        onChange={e => onChange(e.target.value)} required
        style={{ ...S.input, ...(pr ? { paddingRight: '2.5rem' } : {}) }}
        onFocus={focusOn} onBlur={focusOff} />
    </div>
  </div>
);

const SelectField = ({ id, label, value, onChange, icon, children }: {
  id: string; label: string; value: string;
  onChange: (v: string) => void; icon: React.ReactNode; children: React.ReactNode;
}) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
    <label style={S.fieldLabel} htmlFor={id}>{label}</label>
    <div style={S.inputWrap}>
      <div style={S.iconWrap}>{icon}</div>
      <select id={id} value={value} onChange={e => onChange(e.target.value)} required
        style={{ ...S.input, appearance: 'none' as const, cursor: 'pointer' }}
        onFocus={focusOn} onBlur={focusOff}>
        {children}
      </select>
      <div style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', color: '#8c909f' }}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
      </div>
    </div>
  </div>
);
