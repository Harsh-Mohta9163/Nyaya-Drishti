import React, { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Department, fetchDepartments, updateCaseDepartment } from '../api/client';

interface DepartmentOverrideModalProps {
  open: boolean;
  caseId: string;
  currentPrimaryCode?: string | null;
  currentSecondaryCodes?: string[];
  onClose: () => void;
  onSaved: () => void;  // called after successful PATCH so parent can refetch
}

/**
 * Verifier modal for reassigning a case's primary + secondary departments.
 * Matches the existing glassmorphism theme (surface-container/70 + backdrop-blur-xl
 * + primary-blue accents + material-symbols-outlined icons).
 */
export const DepartmentOverrideModal: React.FC<DepartmentOverrideModalProps> = ({
  open,
  caseId,
  currentPrimaryCode,
  currentSecondaryCodes = [],
  onClose,
  onSaved,
}) => {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [primaryCode, setPrimaryCode] = useState<string>(currentPrimaryCode || '');
  const [secondaryCodes, setSecondaryCodes] = useState<string[]>(currentSecondaryCodes || []);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');

  useEffect(() => {
    if (!open) return;
    fetchDepartments()
      .then(setDepartments)
      .catch(err => setError(err.message || 'Failed to load departments'));
    setPrimaryCode(currentPrimaryCode || '');
    setSecondaryCodes(currentSecondaryCodes || []);
    setQuery('');
    setError(null);
  }, [open, currentPrimaryCode, JSON.stringify(currentSecondaryCodes)]);

  const filteredDepts = useMemo(() => {
    if (!query.trim()) return departments;
    const q = query.toLowerCase();
    return departments.filter(d =>
      d.name.toLowerCase().includes(q) ||
      d.code.toLowerCase().includes(q) ||
      d.sector.toLowerCase().includes(q),
    );
  }, [departments, query]);

  const toggleSecondary = (code: string) => {
    if (code === primaryCode) return; // can't tag primary as secondary too
    setSecondaryCodes(prev =>
      prev.includes(code) ? prev.filter(c => c !== code) : [...prev, code],
    );
  };

  const handleSave = async () => {
    if (!primaryCode) {
      setError('Pick a primary department before saving.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await updateCaseDepartment(caseId, primaryCode, secondaryCodes.filter(c => c !== primaryCode));
      onSaved();
      onClose();
    } catch (e: any) {
      setError(e?.message || 'Failed to save department override.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 grid place-items-center p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={e => e.stopPropagation()}
            className="glass-card w-full max-w-2xl max-h-[85vh] flex flex-col"
          >
            {/* Header */}
            <header className="flex items-start justify-between gap-4 p-6 border-b border-outline-variant/30">
              <div className="min-w-0">
                <h2 className="text-xl font-bold text-on-surface tracking-tight">
                  Reassign Department
                </h2>
                <p className="text-on-surface-variant text-xs font-medium mt-1 opacity-70">
                  AI-classified this case as <span className="text-primary-blue font-bold">{currentPrimaryCode || 'UNASSIGNED'}</span>.
                  Override below — your change is audit-logged.
                </p>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest/50 transition-all shrink-0"
                title="Close"
              >
                <span className="material-symbols-outlined text-xl">close</span>
              </button>
            </header>

            {/* Search */}
            <div className="px-6 pt-4 pb-3">
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-lg opacity-60">search</span>
                <input
                  type="text"
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  placeholder="Search 48 departments..."
                  className="w-full pl-10 pr-4 py-2.5 bg-surface-container-high border border-outline-variant/30 rounded-lg text-sm text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary-blue/50 transition-colors"
                />
              </div>
            </div>

            {/* Dept list — scrollable */}
            <div className="flex-1 overflow-y-auto px-6 pb-3 scrollbar-thin">
              {filteredDepts.length === 0 ? (
                <p className="text-on-surface-variant text-sm opacity-60 py-8 text-center">
                  No departments match "{query}"
                </p>
              ) : (
                <ul className="space-y-1.5">
                  {filteredDepts.map(d => {
                    const isPrimary = d.code === primaryCode;
                    const isSecondary = secondaryCodes.includes(d.code);
                    return (
                      <li
                        key={d.code}
                        className={`flex items-center gap-3 p-3 rounded-lg border transition-all ${
                          isPrimary
                            ? 'bg-primary-blue/15 border-primary-blue/40'
                            : isSecondary
                            ? 'bg-surface-container-high border-outline-variant/40'
                            : 'border-outline-variant/15 hover:bg-surface-container-highest/30 hover:border-outline-variant/30'
                        }`}
                      >
                        <button
                          onClick={() => setPrimaryCode(d.code)}
                          title="Set as primary department"
                          className={`shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                            isPrimary
                              ? 'bg-primary-blue border-primary-blue'
                              : 'border-outline-variant hover:border-primary-blue/60'
                          }`}
                        >
                          {isPrimary && <span className="w-2 h-2 rounded-full bg-on-primary-blue" />}
                        </button>
                        <div className="flex-1 min-w-0">
                          <p className="text-on-surface font-bold text-sm truncate">{d.name}</p>
                          <p className="text-on-surface-variant text-[10px] uppercase tracking-widest opacity-60">
                            {d.sector} · <span className="text-primary-blue/80">{d.code}</span>
                          </p>
                        </div>
                        <button
                          onClick={() => toggleSecondary(d.code)}
                          disabled={isPrimary}
                          title={isPrimary ? 'Primary cannot be a secondary too' : isSecondary ? 'Remove as secondary' : 'Tag as secondary'}
                          className={`shrink-0 px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest rounded-md transition-all ${
                            isPrimary
                              ? 'opacity-30 cursor-not-allowed border border-outline-variant/30'
                              : isSecondary
                              ? 'bg-primary-blue/15 text-primary-blue border border-primary-blue/30'
                              : 'border border-outline-variant/30 text-on-surface-variant hover:text-on-surface hover:border-outline-variant'
                          }`}
                        >
                          {isSecondary ? '✓ Tag' : '+ Tag'}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>

            {/* Selection summary + error */}
            <div className="px-6 py-3 border-t border-outline-variant/30 space-y-2">
              <div className="flex items-center gap-2 flex-wrap text-xs">
                <span className="text-on-surface-variant font-bold uppercase tracking-widest opacity-60">Selected:</span>
                {primaryCode ? (
                  <span className="px-2 py-0.5 rounded bg-primary-blue/15 text-primary-blue text-[10px] font-bold uppercase tracking-widest">
                    Primary: {primaryCode}
                  </span>
                ) : (
                  <span className="text-on-surface-variant text-[10px] opacity-50">No primary picked</span>
                )}
                {secondaryCodes.filter(c => c !== primaryCode).map(code => (
                  <span key={code} className="px-2 py-0.5 rounded border border-outline-variant/40 text-on-surface-variant text-[10px] font-bold uppercase tracking-widest">
                    {code}
                  </span>
                ))}
              </div>
              {error && (
                <p className="text-error-red text-xs font-medium">{error}</p>
              )}
            </div>

            {/* Footer */}
            <footer className="flex justify-end gap-2 p-4 border-t border-outline-variant/30">
              <button
                onClick={onClose}
                disabled={saving}
                className="btn-secondary text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !primaryCode}
                className="btn-primary text-sm flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? (
                  <>
                    <span className="material-symbols-outlined text-base animate-spin">progress_activity</span>
                    Saving...
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-base">save</span>
                    Save &amp; Reassign
                  </>
                )}
              </button>
            </footer>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
