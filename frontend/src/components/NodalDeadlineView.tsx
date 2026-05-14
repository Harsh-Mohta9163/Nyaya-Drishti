import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'motion/react';
import { DeadlineRow, fetchDeadlines } from '../api/client';
import { useAuth, isGlobalRole } from '../context/AuthContext';

type Urgency = DeadlineRow['urgency'];

const URGENCY_TONE: Record<Urgency, string> = {
  overdue: 'bg-error-red/15 text-error-red border-error-red/40',
  critical: 'bg-error-red/10 text-error-red border-error-red/30',
  warning: 'bg-amber-500/15 text-amber-300 border-amber-400/30',
  safe: 'bg-emerald-500/15 text-emerald-300 border-emerald-400/30',
  unknown: 'bg-surface-container-highest/70 text-on-surface-variant border-outline-variant/40',
};

const URGENCY_LABEL: Record<Urgency, string> = {
  overdue: 'OVERDUE',
  critical: 'CRITICAL',
  warning: 'WARNING',
  safe: 'ON TRACK',
  unknown: 'NO DEADLINE',
};

const URGENCY_ICON: Record<Urgency, string> = {
  overdue: 'priority_high',
  critical: 'warning',
  warning: 'schedule',
  safe: 'check_circle',
  unknown: 'help',
};

interface Props {
  onSelectCase?: (caseId: string) => void;
}

export const NodalDeadlineView: React.FC<Props> = ({ onSelectCase }) => {
  const { user } = useAuth();
  const [rows, setRows] = useState<DeadlineRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [urgencyFilter, setUrgencyFilter] = useState<Urgency | 'all'>('all');

  useEffect(() => {
    setLoading(true);
    fetchDeadlines()
      .then(setRows)
      .catch(err => setError(err?.message || 'Failed to load deadlines'))
      .finally(() => setLoading(false));
  }, []);

  const counts = useMemo(() => {
    const c = { overdue: 0, critical: 0, warning: 0, safe: 0, unknown: 0, total: 0 };
    rows.forEach(r => {
      c[r.urgency]++;
      c.total++;
    });
    return c;
  }, [rows]);

  const visible = useMemo(() => {
    if (urgencyFilter === 'all') return rows;
    return rows.filter(r => r.urgency === urgencyFilter);
  }, [rows, urgencyFilter]);

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
      <div>
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-on-surface tracking-tighter">
          Deadline Monitor
        </h2>
        <p className="text-on-surface-variant text-base sm:text-lg font-medium opacity-70 mt-1">
          Approved Action Plans tracked by statutory limitation period —{' '}
          <span className="text-on-surface">
            {isGlobalRole(user?.role) ? 'all departments' : user?.department_name || 'your department'}
          </span>
          . Watch the orange and red rows.
        </p>
      </div>

      {/* Stat strip */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
        <StatTile label="Total Active" value={counts.total} icon="event_repeat" tone="text-on-surface" />
        <StatTile label="Overdue" value={counts.overdue} icon="priority_high" tone="text-error-red" />
        <StatTile label="Critical (≤3d)" value={counts.critical} icon="warning" tone="text-error-red" />
        <StatTile label="Warning (≤14d)" value={counts.warning} icon="schedule" tone="text-amber-300" />
        <StatTile label="On Track" value={counts.safe} icon="check_circle" tone="text-emerald-300" />
      </div>

      {/* Urgency filter pills */}
      <div className="flex flex-wrap gap-2">
        <FilterPill active={urgencyFilter === 'all'} onClick={() => setUrgencyFilter('all')} label="All" />
        <FilterPill active={urgencyFilter === 'overdue'} onClick={() => setUrgencyFilter('overdue')} label="Overdue" />
        <FilterPill active={urgencyFilter === 'critical'} onClick={() => setUrgencyFilter('critical')} label="Critical" />
        <FilterPill active={urgencyFilter === 'warning'} onClick={() => setUrgencyFilter('warning')} label="Warning" />
        <FilterPill active={urgencyFilter === 'safe'} onClick={() => setUrgencyFilter('safe')} label="Safe" />
      </div>

      {error && (
        <div className="glass-card p-3 border-l-4 border-error-red/70 text-sm text-error-red">
          {error}
          <button onClick={() => setError(null)} className="ml-3 underline opacity-70 hover:opacity-100">dismiss</button>
        </div>
      )}

      {/* Table-ish list */}
      {visible.length === 0 ? (
        <div className="glass-card p-10 text-center text-on-surface-variant">
          <span className="material-symbols-outlined text-5xl opacity-30 mb-3">event_available</span>
          <p className="text-base font-medium">No deadlines in this view.</p>
          <p className="text-sm opacity-60 mt-1">
            Deadlines appear once HLC approves an Action Plan and the rules engine writes a statutory date.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {visible.map((row, idx) => (
            <DeadlineCard key={`${row.action_plan_id}-${idx}`} row={row} onOpenCase={() => onSelectCase?.(row.case_id)} />
          ))}
        </div>
      )}
    </div>
  );
};

const StatTile: React.FC<{ label: string; value: number; icon: string; tone: string }> = ({ label, value, icon, tone }) => (
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

const DeadlineCard: React.FC<{ row: DeadlineRow; onOpenCase: () => void }> = ({ row, onOpenCase }) => {
  const dr = row.days_remaining;
  const daysText =
    dr === null
      ? '—'
      : dr < 0
      ? `${Math.abs(dr)}d overdue`
      : dr === 0
      ? 'today'
      : `${dr}d left`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-4 sm:p-5 flex flex-col lg:flex-row lg:items-center gap-4"
    >
      {/* Urgency chip */}
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider border self-start shrink-0 ${URGENCY_TONE[row.urgency]}`}
      >
        <span className="material-symbols-outlined text-sm">{URGENCY_ICON[row.urgency]}</span>
        {URGENCY_LABEL[row.urgency]}
      </span>

      {/* Case / context */}
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
        <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-on-surface-variant">
          <span className="flex items-center gap-1">
            <span className="material-symbols-outlined text-[14px]">gavel</span>
            {row.recommendation || 'PENDING'}
          </span>
          {row.statutory_period_type && (
            <span className="flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px]">policy</span>
              {row.statutory_period_type}
            </span>
          )}
          {row.contempt_risk && (
            <span
              className={`flex items-center gap-1 ${
                row.contempt_risk === 'High'
                  ? 'text-error-red'
                  : row.contempt_risk === 'Medium'
                  ? 'text-amber-300'
                  : 'text-on-surface-variant'
              }`}
            >
              <span className="material-symbols-outlined text-[14px]">shield</span>
              contempt: {row.contempt_risk}
            </span>
          )}
        </div>
      </div>

      {/* Deadline column */}
      <div className="lg:text-right shrink-0">
        <p className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant opacity-60">
          {row.next_deadline_label || 'Next deadline'}
        </p>
        <p className="text-xl font-bold text-on-surface tracking-tight">
          {row.next_deadline || '—'}
        </p>
        <p
          className={`text-xs font-semibold ${
            row.urgency === 'overdue' || row.urgency === 'critical'
              ? 'text-error-red'
              : row.urgency === 'warning'
              ? 'text-amber-300'
              : row.urgency === 'safe'
              ? 'text-emerald-300'
              : 'text-on-surface-variant'
          }`}
        >
          {daysText}
        </p>
      </div>
    </motion.div>
  );
};
