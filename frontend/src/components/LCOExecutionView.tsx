import React, { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  DirectiveExecution,
  ExecutionStatus,
  fetchExecutions,
  updateExecution,
} from '../api/client';
import { useAuth, isGlobalRole } from '../context/AuthContext';

const STATUS_LABELS: Record<ExecutionStatus, string> = {
  pending: 'Pending',
  in_progress: 'In Progress',
  completed: 'Completed',
  blocked: 'Blocked',
};

const STATUS_TONE: Record<ExecutionStatus, string> = {
  pending: 'bg-surface-container-highest/70 text-on-surface-variant border-outline-variant/40',
  in_progress: 'bg-primary-blue/15 text-primary-blue border-primary-blue/30',
  completed: 'bg-emerald-500/15 text-emerald-300 border-emerald-400/30',
  blocked: 'bg-error-red/15 text-error-red border-error-red/40',
};

const STATUS_ICONS: Record<ExecutionStatus, string> = {
  pending: 'pending',
  in_progress: 'autorenew',
  completed: 'check_circle',
  blocked: 'block',
};

interface Props {
  onSelectCase?: (caseId: string) => void;
}

export const LCOExecutionView: React.FC<Props> = ({ onSelectCase }) => {
  const { user } = useAuth();
  const [rows, setRows] = useState<DirectiveExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<ExecutionStatus | 'all'>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = () => {
    setLoading(true);
    fetchExecutions({ status: statusFilter === 'all' ? null : statusFilter })
      .then(setRows)
      .catch(err => setError(err?.message || 'Failed to load executions'))
      .finally(() => setLoading(false));
  };

  useEffect(loadData, [statusFilter]);

  const counts = useMemo(() => {
    const c = { pending: 0, in_progress: 0, completed: 0, blocked: 0, total: 0 };
    rows.forEach(r => {
      c[r.status]++;
      c.total++;
    });
    return c;
  }, [rows]);

  // When a status filter is active, rows are already filtered server-side;
  // when "all", group them visually by status for at-a-glance scanning.
  const grouped = useMemo(() => {
    const m = new Map<ExecutionStatus, DirectiveExecution[]>();
    rows.forEach(r => {
      const arr = m.get(r.status) || [];
      arr.push(r);
      m.set(r.status, arr);
    });
    const order: ExecutionStatus[] = ['blocked', 'in_progress', 'pending', 'completed'];
    return order.filter(s => m.has(s)).map(s => [s, m.get(s)!] as const);
  }, [rows]);

  const showToast = (msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast(null), 2500);
  };

  const handleStatusChange = async (row: DirectiveExecution, newStatus: ExecutionStatus) => {
    try {
      const updated = await updateExecution(row.id, { status: newStatus });
      setRows(prev => prev.map(r => (r.id === row.id ? updated : r)));
      showToast(`Marked "${STATUS_LABELS[newStatus]}"`);
    } catch (e: any) {
      setError(e?.message || 'Update failed');
    }
  };

  const handleNotesSave = async (row: DirectiveExecution, notes: string) => {
    try {
      const updated = await updateExecution(row.id, { notes });
      setRows(prev => prev.map(r => (r.id === row.id ? updated : r)));
      showToast('Notes saved');
    } catch (e: any) {
      setError(e?.message || 'Update failed');
    }
  };

  const handleProofUpload = async (row: DirectiveExecution, file: File) => {
    try {
      const updated = await updateExecution(row.id, { proof_file: file });
      setRows(prev => prev.map(r => (r.id === row.id ? updated : r)));
      showToast('Proof uploaded');
    } catch (e: any) {
      setError(e?.message || 'Upload failed');
    }
  };

  if (loading) {
    return (
      <div className="py-10 flex items-center justify-center h-64">
        <span className="material-symbols-outlined text-4xl animate-spin text-primary-blue opacity-40">progress_activity</span>
      </div>
    );
  }

  return (
    <div className="py-6 sm:py-10 space-y-6 max-w-[1440px] mx-auto">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
        <div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-on-surface tracking-tighter">
            Execution Dashboard
          </h2>
          <p className="text-on-surface-variant text-base sm:text-lg font-medium opacity-70 mt-1">
            Court directions approved by the Head of Legal Cell — awaiting physical execution by{' '}
            <span className="text-on-surface">
              {isGlobalRole(user?.role) ? 'all departments' : user?.department_name || 'your department'}
            </span>
            .
          </p>
        </div>
      </div>

      {/* Stat strip */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
        <StatCard label="Total Directions" value={counts.total} icon="checklist_rtl" tone="text-on-surface" />
        <StatCard label="Pending" value={counts.pending} icon="pending" tone="text-on-surface" />
        <StatCard label="In Progress" value={counts.in_progress} icon="autorenew" tone="text-primary-blue" />
        <StatCard label="Completed" value={counts.completed} icon="check_circle" tone="text-emerald-300" />
        <StatCard label="Blocked" value={counts.blocked} icon="block" tone="text-error-red" />
      </div>

      {/* Status filter pills */}
      <div className="flex flex-wrap gap-2">
        <FilterPill active={statusFilter === 'all'} onClick={() => setStatusFilter('all')} label="All" />
        <FilterPill active={statusFilter === 'pending'} onClick={() => setStatusFilter('pending')} label="Pending" />
        <FilterPill active={statusFilter === 'in_progress'} onClick={() => setStatusFilter('in_progress')} label="In Progress" />
        <FilterPill active={statusFilter === 'completed'} onClick={() => setStatusFilter('completed')} label="Completed" />
        <FilterPill active={statusFilter === 'blocked'} onClick={() => setStatusFilter('blocked')} label="Blocked" />
      </div>

      {/* Error banner */}
      {error && (
        <div className="glass-card p-3 border-l-4 border-error-red/70 text-sm text-error-red">
          {error}
          <button onClick={() => setError(null)} className="ml-3 underline opacity-70 hover:opacity-100">dismiss</button>
        </div>
      )}

      {/* List */}
      {rows.length === 0 ? (
        <div className="glass-card p-10 text-center text-on-surface-variant">
          <span className="material-symbols-outlined text-5xl opacity-30 mb-3">inbox</span>
          <p className="text-base font-medium">No approved directives in this view.</p>
          <p className="text-sm opacity-60 mt-1">
            Directives appear here only after the HLC approves the Action Plan in the Verify tab.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {grouped.map(([status, items]) => (
            <section key={status} className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant opacity-70 flex items-center gap-2">
                <span className="material-symbols-outlined text-base">{STATUS_ICONS[status]}</span>
                {STATUS_LABELS[status]} <span className="opacity-50">· {items.length}</span>
              </h3>
              <div className="space-y-3">
                {items.map(row => (
                  <ExecutionCard
                    key={row.id}
                    row={row}
                    expanded={expandedId === row.id}
                    onToggle={() => setExpandedId(prev => (prev === row.id ? null : row.id))}
                    onStatusChange={s => handleStatusChange(row, s)}
                    onNotesSave={n => handleNotesSave(row, n)}
                    onProofUpload={f => handleProofUpload(row, f)}
                    onOpenCase={() => onSelectCase?.(row.case_id)}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-6 right-6 z-50 glass-card px-4 py-3 text-sm text-on-surface flex items-center gap-2 border-emerald-400/30"
          >
            <span className="material-symbols-outlined text-emerald-300">check_circle</span>
            {toast}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// ─── Sub-components ──────────────────────────────────────────────────────────

const StatCard: React.FC<{ label: string; value: number; icon: string; tone: string }> = ({
  label, value, icon, tone,
}) => (
  <div className="glass-card p-4 flex items-center gap-3">
    <span className={`material-symbols-outlined text-3xl ${tone} opacity-80`}>{icon}</span>
    <div className="min-w-0">
      <p className="text-on-surface-variant text-[10px] font-bold uppercase tracking-widest opacity-60 truncate">{label}</p>
      <h3 className={`text-2xl font-bold ${tone} tracking-tight`}>{value}</h3>
    </div>
  </div>
);

const FilterPill: React.FC<{ active: boolean; onClick: () => void; label: string }> = ({ active, onClick, label }) => (
  <button
    onClick={onClick}
    className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
      active
        ? 'bg-primary-blue/15 text-primary-blue border-primary-blue/30'
        : 'bg-surface-container/40 text-on-surface-variant border-outline-variant/30 hover:text-on-surface'
    }`}
  >
    {label}
  </button>
);

interface CardProps {
  row: DirectiveExecution;
  expanded: boolean;
  onToggle: () => void;
  onStatusChange: (s: ExecutionStatus) => void;
  onNotesSave: (notes: string) => void;
  onProofUpload: (file: File) => void;
  onOpenCase: () => void;
}

const ExecutionCard: React.FC<CardProps> = ({
  row, expanded, onToggle, onStatusChange, onNotesSave, onProofUpload, onOpenCase,
}) => {
  const [draftNotes, setDraftNotes] = useState(row.notes || '');

  useEffect(() => { setDraftNotes(row.notes || ''); }, [row.notes]);

  return (
    <div className="glass-card overflow-hidden">
      {/* Collapsed header row — always visible */}
      <div className="p-4 sm:p-5 flex items-start gap-4">
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border ${STATUS_TONE[row.status]}`}>
          <span className="material-symbols-outlined text-xs">{STATUS_ICONS[row.status]}</span>
          {STATUS_LABELS[row.status]}
        </span>

        <div className="flex-grow min-w-0">
          <div className="flex flex-wrap items-baseline gap-2">
            <button
              onClick={onOpenCase}
              className="text-sm font-semibold text-primary-blue hover:underline truncate max-w-[40ch]"
              title={row.case_title}
            >
              {row.case_number}
            </button>
            <span className="text-xs text-on-surface-variant truncate max-w-[50ch]" title={row.case_title}>
              {row.case_title}
            </span>
            {row.department_code && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-container-highest/60 text-on-surface-variant border border-outline-variant/30">
                {row.department_code}
              </span>
            )}
          </div>

          <p className="mt-2 text-on-surface text-sm leading-relaxed line-clamp-2">
            {row.govt_summary || row.action_required || row.directive_text || '(no action text)'}
          </p>

          <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-on-surface-variant">
            {row.responsible_entity && (
              <span className="flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">person</span>
                {row.responsible_entity}
              </span>
            )}
            {row.deadline_mentioned && (
              <span className="flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">schedule</span>
                {row.deadline_mentioned}
              </span>
            )}
            {row.compliance_deadline && (
              <span className="flex items-center gap-1 text-on-surface">
                <span className="material-symbols-outlined text-[14px]">event</span>
                deadline: {row.compliance_deadline}
              </span>
            )}
            {row.executed_by_name && row.status === 'completed' && (
              <span className="flex items-center gap-1 text-emerald-300">
                <span className="material-symbols-outlined text-[14px]">verified</span>
                done by {row.executed_by_name}
              </span>
            )}
          </div>
        </div>

        <button
          onClick={onToggle}
          className="p-2 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest/50 transition-all shrink-0"
          title={expanded ? 'Collapse' : 'Expand'}
        >
          <span className={`material-symbols-outlined text-xl transition-transform ${expanded ? 'rotate-180' : ''}`}>
            expand_more
          </span>
        </button>
      </div>

      {/* Expanded body */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden border-t border-outline-variant/20"
          >
            <div className="p-4 sm:p-5 space-y-4">
              {/* Implementation steps come FIRST — that's what the LCO needs to act on. */}
              {row.gov_action_required && row.implementation_steps && row.implementation_steps.length > 0 && (
                <div className="bg-emerald-500/[0.06] border border-emerald-400/30 rounded-lg p-3">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-300/80 mb-2 flex items-center gap-1">
                    <span className="material-symbols-outlined text-base">play_arrow</span>
                    Implementation Steps
                  </p>
                  <ol className="space-y-1.5 text-sm text-on-surface-variant leading-relaxed list-decimal list-inside">
                    {row.implementation_steps.map((step, i) => (
                      <li key={i} className="marker:text-emerald-300/70">{step}</li>
                    ))}
                  </ol>
                </div>
              )}

              {row.directive_text && (
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant opacity-70 mb-1">
                    Court Direction (verbatim)
                  </p>
                  <p className="text-sm text-on-surface leading-relaxed whitespace-pre-wrap">{row.directive_text}</p>
                </div>
              )}

              {/* Status action row */}
              <div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant opacity-70 mb-2">
                  Update Status
                </p>
                <div className="flex flex-wrap gap-2">
                  {(['pending', 'in_progress', 'completed', 'blocked'] as ExecutionStatus[]).map(s => (
                    <button
                      key={s}
                      onClick={() => onStatusChange(s)}
                      disabled={row.status === s}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                        row.status === s
                          ? `${STATUS_TONE[s]} cursor-default opacity-90`
                          : 'bg-surface-container/40 text-on-surface-variant border-outline-variant/30 hover:text-on-surface hover:border-outline-variant/60'
                      }`}
                    >
                      <span className="material-symbols-outlined text-sm align-middle mr-1">{STATUS_ICONS[s]}</span>
                      {STATUS_LABELS[s]}
                    </button>
                  ))}
                </div>
              </div>

              {/* Notes */}
              <div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant opacity-70 mb-1">
                  LCO Notes
                </p>
                <textarea
                  value={draftNotes}
                  onChange={e => setDraftNotes(e.target.value)}
                  rows={2}
                  className="w-full bg-surface-container/60 border border-outline-variant/30 rounded-lg px-3 py-2 text-sm text-on-surface focus:outline-none focus:border-primary-blue/50"
                  placeholder="Add execution notes — e.g., payment reference, file diary number, blocker reason…"
                />
                <div className="flex justify-end mt-2">
                  <button
                    onClick={() => onNotesSave(draftNotes)}
                    disabled={draftNotes === (row.notes || '')}
                    className="px-3 py-1.5 rounded-lg bg-primary-blue/15 text-primary-blue text-xs font-semibold border border-primary-blue/30 hover:bg-primary-blue/25 disabled:opacity-40 disabled:cursor-default transition-all"
                  >
                    Save notes
                  </button>
                </div>
              </div>

              {/* Proof upload */}
              <div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant opacity-70 mb-1">
                  Proof of Compliance
                </p>
                {row.proof_file_url ? (
                  <a
                    href={row.proof_file_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 text-sm text-primary-blue hover:underline"
                  >
                    <span className="material-symbols-outlined text-base">description</span>
                    View uploaded proof
                  </a>
                ) : (
                  <p className="text-xs text-on-surface-variant opacity-70 mb-2">No proof uploaded yet.</p>
                )}
                <label className="mt-2 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-container/60 border border-outline-variant/30 text-xs font-semibold text-on-surface-variant hover:text-on-surface cursor-pointer transition-all">
                  <span className="material-symbols-outlined text-sm">upload_file</span>
                  {row.proof_file_url ? 'Replace proof' : 'Upload proof'}
                  <input
                    type="file"
                    className="hidden"
                    onChange={e => {
                      const f = e.target.files?.[0];
                      if (f) onProofUpload(f);
                      if (e.target) e.target.value = '';
                    }}
                  />
                </label>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
