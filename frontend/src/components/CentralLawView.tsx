import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  DeptDashboardRow,
  DirectiveExecution,
  DeadlineRow,
  DashboardStats,
  fetchByDepartmentDashboard,
  fetchExecutions,
  fetchDeadlines,
  fetchDashboardStats,
} from '../api/client';

// ── Props ─────────────────────────────────────────────────────────────────────

interface CentralLawViewProps {
  onSelectDepartment: (deptCode: string) => void;
  onNavigate?: (view: 'cases' | 'deadlines' | 'execution' | 'dashboard') => void;
}

// ── Color tokens (design-matched, muted palette for dark bg) ─────────────────

const SEG: Record<string, string> = {
  amber:   '#C29465',
  blue:    '#7595D2',
  teal:    '#6DA8A0',
  emerald: '#6FB291',
  red:     '#C57979',
  violet:  '#9789C2',
};

const TONE: Record<string, { bg: string; border: string; text: string }> = {
  neutral: { bg: 'rgba(255,255,255,0.05)', border: 'rgba(255,255,255,0.10)', text: '#c2c6d6' },
  blue:    { bg: 'rgba(117,149,210,0.12)', border: 'rgba(117,149,210,0.28)', text: '#adc6ff' },
  emerald: { bg: 'rgba(111,178,145,0.12)', border: 'rgba(111,178,145,0.28)', text: '#6FB291' },
  amber:   { bg: 'rgba(194,148,101,0.12)', border: 'rgba(194,148,101,0.28)', text: '#C29465' },
  red:     { bg: 'rgba(197,121,121,0.12)', border: 'rgba(197,121,121,0.28)', text: '#C57979' },
  teal:    { bg: 'rgba(109,168,160,0.12)', border: 'rgba(109,168,160,0.28)', text: '#6DA8A0' },
};

const URGENCY_COLOR: Record<string, string> = {
  overdue:  '#C57979',
  critical: '#C57979',
  warning:  '#C29465',
  safe:     '#6FB291',
  unknown:  '#525A6B',
};

// ── Shared atoms ──────────────────────────────────────────────────────────────

function Icon({ name, className = 'w-4 h-4' }: { name: string; className?: string }) {
  const p = { className, fill: 'none' as const, viewBox: '0 0 24 24', stroke: 'currentColor', strokeWidth: 1.6, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
  switch (name) {
    case 'folder':      return <svg {...p}><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z"/></svg>;
    case 'clock':       return <svg {...p}><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>;
    case 'alert':       return <svg {...p}><path d="M12 2 2 21h20L12 2Z"/><path d="M12 10v4M12 18h.01"/></svg>;
    case 'shield':      return <svg {...p}><path d="M12 3 4 6v6c0 4.5 3.2 8.4 8 9 4.8-.6 8-4.5 8-9V6l-8-3Z"/></svg>;
    case 'bolt':        return <svg {...p}><path d="m13 2-8 12h6l-1 8 8-12h-6l1-8Z"/></svg>;
    case 'trending':    return <svg {...p}><path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/></svg>;
    case 'arrow-right': return <svg {...p}><path d="M5 12h14M13 5l7 7-7 7"/></svg>;
    case 'x':           return <svg {...p}><path d="M6 6l12 12M18 6 6 18"/></svg>;
    case 'chev-down':   return <svg {...p}><path d="m6 9 6 6 6-6"/></svg>;
    case 'chev-right':  return <svg {...p}><path d="m9 6 6 6-6 6"/></svg>;
    case 'reload':      return <svg {...p}><path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/><path d="M3 21v-5h5"/></svg>;
    case 'check':       return <svg {...p}><path d="m20 6-11 11-5-5"/></svg>;
    case 'building':    return <svg {...p}><rect x="4" y="3" width="16" height="18" rx="1"/><path d="M9 7h.01M9 11h.01M9 15h.01M15 7h.01M15 11h.01M15 15h.01"/></svg>;
    default: return null;
  }
}

function ProgressBar({ value, max = 100, color = 'blue', height = 5 }: {
  value: number; max?: number; color?: string; height?: number;
}) {
  const pct = Math.max(0, Math.min(100, max > 0 ? (value / max) * 100 : 0));
  return (
    <div className="w-full rounded-full overflow-hidden" style={{ height, background: 'rgba(255,255,255,0.06)' }}>
      <div className="h-full rounded-full transition-all duration-700"
        style={{ width: `${pct}%`, background: SEG[color] || SEG.blue }} />
    </div>
  );
}

function StackedBar({ segments, height = 6 }: {
  segments: { value: number; color: string }[]; height?: number;
}) {
  const total = Math.max(1, segments.reduce((a, s) => a + (s.value || 0), 0));
  return (
    <div className="w-full rounded-full overflow-hidden flex" style={{ height, background: 'rgba(255,255,255,0.05)' }}>
      {segments.map((s, i) => s.value > 0 ? (
        <div key={i} className="h-full transition-all duration-700"
          style={{ width: `${(s.value / total) * 100}%`, background: SEG[s.color] }}
          title={`${s.color}: ${s.value}`} />
      ) : null)}
    </div>
  );
}

function PillBadge({ tone = 'neutral', children, small = false }: {
  tone?: string; children: React.ReactNode; small?: boolean;
}) {
  const c = TONE[tone] || TONE.neutral;
  return (
    <span className={`inline-flex items-center gap-1 font-semibold uppercase tracking-wider rounded-full border ${small ? 'px-1.5 py-0.5 text-[9px]' : 'px-2 py-0.5 text-[10px]'}`}
      style={{ background: c.bg, borderColor: c.border, color: c.text }}>
      {children}
    </span>
  );
}

function Card({ className = '', children, onClick }: {
  className?: string; children: React.ReactNode; onClick?: () => void;
}) {
  const base = 'rounded-xl border bg-surface-container/60 backdrop-blur-sm';
  if (onClick) {
    return (
      <button onClick={onClick}
        className={`${base} border-outline-variant/30 hover:bg-surface-container-high/70 hover:border-outline-variant/50 transition-all text-left ${className}`}>
        {children}
      </button>
    );
  }
  return (
    <div className={`${base} border-outline-variant/20 ${className}`}>
      {children}
    </div>
  );
}

function ZoneHeader({ title, sub, right, size = 'panel' }: {
  title: string; sub?: string; right?: React.ReactNode; size?: 'section' | 'panel';
}) {
  return (
    <div className={`flex items-end justify-between gap-4 ${size === 'section' ? 'mb-5' : 'mb-4'}`}>
      <div>
        <h2 className={size === 'section'
          ? 'text-xl sm:text-2xl font-bold tracking-tight text-on-surface'
          : 'text-[15px] font-semibold tracking-tight text-on-surface'}>
          {title}
        </h2>
        {sub && <p className="mt-0.5 text-[12px] text-on-surface-variant/70">{sub}</p>}
      </div>
      {right && <div className="shrink-0">{right}</div>}
    </div>
  );
}

// ── Data derivation helpers ───────────────────────────────────────────────────

interface DeptExecStats {
  deptCode: string;
  deptName: string;
  assigned: number;
  completed: number;
  completedWithProof: number;
  inProgress: number;
  pending: number;
  blocked: number;
}

function computeExecByDept(execs: DirectiveExecution[]): Map<string, DeptExecStats> {
  const map = new Map<string, DeptExecStats>();
  execs.forEach(e => {
    const code = e.department_code || 'UNKNOWN';
    const prev = map.get(code) || {
      deptCode: code, deptName: e.department_name || code,
      assigned: 0, completed: 0, completedWithProof: 0,
      inProgress: 0, pending: 0, blocked: 0,
    };
    prev.assigned++;
    if (e.status === 'completed') {
      prev.completed++;
      if (e.proof_file) prev.completedWithProof++;
    } else if (e.status === 'in_progress') {
      prev.inProgress++;
    } else if (e.status === 'pending') {
      prev.pending++;
    } else if (e.status === 'blocked') {
      prev.blocked++;
    }
    map.set(code, prev);
  });
  return map;
}

// ── Zone 1: KPI tiles ─────────────────────────────────────────────────────────

interface KpiTileProps {
  label: string;
  value: number | string;
  sub: string;
  tone?: string;
  icon: string;
  badge?: string;
  onClick?: () => void;
}

function KpiTile({ label, value, sub, tone = 'neutral', icon, badge, onClick }: KpiTileProps) {
  const c = TONE[tone] || TONE.neutral;
  return (
    <button onClick={onClick}
      className="relative text-left rounded-xl bg-surface-container/60 border border-outline-variant/20 px-4 pt-4 pb-3.5 transition hover:bg-surface-container-high/70 hover:border-outline-variant/40 group overflow-hidden w-full">
      {tone !== 'neutral' && (
        <div className="absolute left-0 top-3 bottom-3 w-[3px] rounded-full" style={{ background: c.text }} />
      )}
      <div className="flex items-start justify-between gap-3">
        <div className="text-[11px] font-medium tracking-wide text-on-surface-variant/70">{label}</div>
        <div className="flex items-center gap-1.5">
          {badge && <PillBadge tone={tone}>{badge}</PillBadge>}
          <span style={{ color: c.text }}><Icon name={icon} className="w-3.5 h-3.5" /></span>
        </div>
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <div className="text-3xl font-bold tracking-tight text-on-surface tabular-nums">{value}</div>
      </div>
      <div className="mt-1.5 text-[11px] text-on-surface-variant/60 leading-tight">{sub}</div>
    </button>
  );
}

function Zone1({ stats, executions, deadlines, onNavigate }: {
  stats: DashboardStats | null;
  executions: DirectiveExecution[];
  deadlines: DeadlineRow[];
  onNavigate?: CentralLawViewProps['onNavigate'];
}) {
  const overdueCount = deadlines.filter(d => d.urgency === 'overdue').length;
  const blockedCount = executions.filter(e => e.status === 'blocked').length;
  const proofGap = executions.filter(e => e.status === 'completed' && !e.proof_file).length;
  const pendingExecCases = new Set(executions.filter(e => e.status === 'pending' || e.status === 'in_progress').map(e => e.case_id)).size;

  const tiles: KpiTileProps[] = [
    {
      id: 'total',
      label: 'Total Active Cases',
      value: stats?.total_cases ?? '—',
      sub: 'Statewide litigation portfolio',
      icon: 'folder',
      tone: 'neutral',
    },
    {
      id: 'pending',
      label: 'Awaiting HLC Verification',
      value: stats?.pending_review ?? '—',
      sub: 'Cases pending human review',
      icon: 'clock',
      tone: (stats?.pending_review ?? 0) > 0 ? 'amber' : 'neutral',
      badge: (stats?.pending_review ?? 0) > 0 ? 'SLA' : undefined,
      onClick: () => onNavigate?.('cases'),
    },
    {
      id: 'exec',
      label: 'Approved, Pending Execution',
      value: pendingExecCases,
      sub: 'Cases with outstanding LCO tasks',
      icon: 'bolt',
      tone: 'blue',
      onClick: () => onNavigate?.('execution'),
    },
    {
      id: 'overdue',
      label: 'Deadline Breached',
      value: overdueCount,
      sub: `Statutory deadline passed`,
      icon: 'alert',
      tone: overdueCount > 0 ? 'red' : 'neutral',
      badge: overdueCount > 0 ? `${overdueCount}` : undefined,
      onClick: () => onNavigate?.('deadlines'),
    },
    {
      id: 'proofgap',
      label: 'Proof Verification Gap',
      value: proofGap,
      sub: 'Completions without proof file',
      icon: 'shield',
      tone: proofGap > 0 ? 'amber' : 'neutral',
      onClick: () => onNavigate?.('execution'),
    },
  ] as any[];

  return (
    <section>
      <ZoneHeader title="System overview" size="section" />
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {tiles.map((tile: any) => (
          <KpiTile key={tile.id} {...tile} />
        ))}
      </div>
    </section>
  );
}

// ── Zone 2: Workload + Comply/Appeal ──────────────────────────────────────────

function WorkloadPanel({ deptRows, onSelectDept }: {
  deptRows: DeptDashboardRow[];
  onSelectDept: (code: string) => void;
}) {
  const [sort, setSort] = useState<'volume' | 'overdue'>('volume');
  const [showAll, setShowAll] = useState(false);

  const rows = useMemo(() => {
    let list = deptRows
      .filter(d => showAll || d.total_cases > 0)
      .map(d => ({
        code: d.code, name: d.name, total: d.total_cases,
        segments: [
          { value: d.pending,                                color: 'amber'   },
          { value: Math.max(0, d.total_cases - d.pending - d.high_risk), color: 'teal' },
          { value: d.high_risk,                              color: 'red'     },
        ],
        overdue: d.high_risk,
      }));
    list.sort((a, b) => sort === 'overdue'
      ? (b.overdue - a.overdue) || (b.total - a.total)
      : b.total - a.total);
    return list;
  }, [deptRows, sort, showAll]);

  const maxTotal = Math.max(...rows.map(r => r.total), 1);
  const hiddenCount = deptRows.filter(d => d.total_cases === 0).length;

  return (
    <Card className="p-5 h-full">
      <ZoneHeader
        title="Department workload"
        sub="Pending verify · In execution · High risk"
        right={
          <div className="flex items-center gap-2">
            <div className="inline-flex items-center gap-0.5 p-0.5 rounded-lg bg-white/5 ring-1 ring-white/8">
              {(['volume', 'overdue'] as const).map(v => (
                <button key={v} onClick={() => setSort(v)}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition ${sort === v ? 'bg-surface-container-highest text-on-surface' : 'text-on-surface-variant/60 hover:text-on-surface'}`}>
                  {v === 'volume' ? 'By volume' : 'By risk'}
                </button>
              ))}
            </div>
            {hiddenCount > 0 && (
              <button onClick={() => setShowAll(v => !v)}
                className="text-[11px] text-on-surface-variant/60 hover:text-on-surface px-2 py-1 rounded-md ring-1 ring-outline-variant/30">
                {showAll ? 'Hide empty' : `+${hiddenCount} more`}
              </button>
            )}
          </div>
        }
      />
      <div className="space-y-4 max-h-[380px] overflow-y-auto scrollbar-thin pr-1">
        {rows.map(r => (
          <button key={r.code} onClick={() => onSelectDept(r.code)} className="block w-full text-left group">
            <div className="flex items-center justify-between text-[11.5px] mb-1.5">
              <span className="text-on-surface-variant font-medium group-hover:text-on-surface transition">{r.name}</span>
              <span className="tabular-nums text-on-surface-variant/50 group-hover:text-on-surface-variant text-[10.5px]">
                {r.total}{r.overdue > 0 ? <span style={{ color: SEG.red }}> · {r.overdue} risk</span> : null}
              </span>
            </div>
            <div style={{ width: `${Math.max(8, (r.total / maxTotal) * 100)}%` }}>
              <StackedBar segments={r.segments} height={8} />
            </div>
          </button>
        ))}
      </div>
      <div className="mt-4 pt-4 border-t border-outline-variant/20 flex flex-wrap gap-x-4 gap-y-1.5 text-[10.5px] text-on-surface-variant/50">
        {[['amber','Pending verify'],['teal','In execution'],['red','High risk']].map(([c,l]) => (
          <span key={c} className="inline-flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm" style={{ background: SEG[c] }}/> {l}
          </span>
        ))}
      </div>
    </Card>
  );
}

function ComplyAppealPanel({ deadlines, deptRows, onSelectDept }: {
  deadlines: DeadlineRow[];
  deptRows: DeptDashboardRow[];
  onSelectDept: (code: string) => void;
}) {
  const [selected, setSelected] = useState('state');

  const { comply, appeal, undecided } = useMemo(() => {
    const src = selected === 'state'
      ? deadlines
      : deadlines.filter(d => d.department_code === selected || d.secondary_departments?.includes(selected));
    const comply = src.filter(d => d.recommendation?.toLowerCase() === 'comply').length;
    const appeal = src.filter(d => d.recommendation?.toLowerCase() === 'appeal').length;
    const undecided = src.length - comply - appeal;
    return { comply, appeal, undecided };
  }, [deadlines, selected]);

  const total = Math.max(1, comply + appeal + undecided);
  const R = 52, C_val = 2 * Math.PI * R;
  let offset = 0;
  const arcs = [
    { label: 'Comply',    value: comply,   color: SEG.emerald },
    { label: 'Appeal',    value: appeal,   color: SEG.blue },
    { label: 'Undecided', value: undecided, color: SEG.amber },
  ];

  const topUndecided = useMemo(() => {
    const byDept = new Map<string, number>();
    deadlines.filter(d => !['comply','appeal'].includes(d.recommendation?.toLowerCase() || ''))
      .forEach(d => {
        const code = d.department_code || '';
        byDept.set(code, (byDept.get(code) || 0) + 1);
      });
    return [...byDept.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 4)
      .map(([code, count]) => ({
        code,
        name: deptRows.find(r => r.code === code)?.name || code,
        count,
      }));
  }, [deadlines, deptRows]);

  return (
    <Card className="p-5 h-full flex flex-col">
      <ZoneHeader title="Comply vs Appeal" sub="Post-approval decisions by scope." />
      <div className="flex items-center gap-2 mb-4">
        <label className="text-[11px] text-on-surface-variant/60 shrink-0">View:</label>
        <select value={selected} onChange={e => setSelected(e.target.value)}
          className="flex-1 bg-surface-container-highest border border-outline-variant/30 rounded-md px-3 py-2 text-[12px] text-on-surface focus:outline-none focus:ring-1 focus:ring-primary-blue/50"
          style={{ appearance: 'none', backgroundImage: `url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23c2c6d6' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polyline points='6 9 12 15 18 9'/></svg>")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 8px center', paddingRight: 24 }}>
          <option value="state">Statewide (all departments)</option>
          <optgroup label="Departments">
            {deptRows.filter(d => d.total_cases > 0).map(d =>
              <option key={d.code} value={d.code}>{d.name}</option>
            )}
          </optgroup>
        </select>
      </div>

      <div className="flex items-center gap-5">
        <div className="relative w-[140px] h-[140px] shrink-0">
          <svg viewBox="0 0 140 140" className="w-full h-full -rotate-90">
            <circle cx="70" cy="70" r={R} stroke="rgba(255,255,255,0.06)" strokeWidth="16" fill="none"/>
            {arcs.map((a, i) => {
              const len = (a.value / total) * C_val;
              const node = (
                <circle key={i} cx="70" cy="70" r={R} stroke={a.color} strokeWidth="16" fill="none"
                  strokeDasharray={`${len} ${C_val - len}`} strokeDashoffset={-offset}
                  strokeLinecap="butt" className="transition-all"/>
              );
              offset += len;
              return node;
            })}
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="text-2xl font-bold tracking-tight text-on-surface tabular-nums">{comply + appeal + undecided}</div>
            <div className="text-[10px] text-on-surface-variant/50 uppercase tracking-wider mt-0.5">plans</div>
          </div>
        </div>
        <div className="flex-1 space-y-2.5">
          {arcs.map(a => (
            <div key={a.label} className="flex items-center justify-between text-[12px]">
              <span className="inline-flex items-center gap-2 text-on-surface-variant">
                <span className="w-2.5 h-2.5 rounded-sm" style={{ background: a.color }}/>
                {a.label}
              </span>
              <span className="tabular-nums text-on-surface font-medium">
                {a.value} <span className="text-on-surface-variant/40 font-normal">({Math.round((a.value / total) * 100)}%)</span>
              </span>
            </div>
          ))}
        </div>
      </div>

      {topUndecided.length > 0 && (
        <div className="mt-4 pt-4 border-t border-outline-variant/20">
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-on-surface-variant/50 mb-2.5">Most undecided · statewide</div>
          <ul className="space-y-1.5">
            {topUndecided.map((d, i) => (
              <li key={d.code} className="flex items-center gap-3 text-[11.5px]">
                <span className="tabular-nums text-on-surface-variant/40 w-3 text-right">{i + 1}</span>
                <button onClick={() => onSelectDept(d.code)}
                  className="flex-1 text-left text-on-surface-variant hover:text-on-surface truncate transition">
                  {d.name.replace(' Department', '')}
                </button>
                <span className="tabular-nums font-medium shrink-0" style={{ color: SEG.amber }}>{d.count} undecided</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}

function Zone2({ deptRows, deadlines, onSelectDept }: {
  deptRows: DeptDashboardRow[];
  deadlines: DeadlineRow[];
  onSelectDept: (code: string) => void;
}) {
  return (
    <section>
      <ZoneHeader title="Workload and decisions" size="section" />
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3">
        <div className="lg:col-span-7"><WorkloadPanel deptRows={deptRows} onSelectDept={onSelectDept} /></div>
        <div className="lg:col-span-5"><ComplyAppealPanel deadlines={deadlines} deptRows={deptRows} onSelectDept={onSelectDept} /></div>
      </div>
    </section>
  );
}

// ── Zone 3: Execution league + Cross-dept coordination ────────────────────────

function LeaguePanel({ execByDept, onSelectDept }: {
  execByDept: Map<string, DeptExecStats>;
  onSelectDept: (code: string) => void;
}) {
  const rows = useMemo(() => {
    return [...execByDept.values()]
      .filter(d => d.assigned >= 3)
      .map(d => ({
        ...d,
        completionPct: Math.round((d.completed / d.assigned) * 100),
        proofPct: d.completed > 0 ? Math.round((d.completedWithProof / d.completed) * 100) : 0,
      }))
      .sort((a, b) => a.completionPct - b.completionPct)
      .slice(0, 8);
  }, [execByDept]);

  if (rows.length === 0) {
    return (
      <Card className="p-5 h-full flex items-center justify-center">
        <p className="text-on-surface-variant/50 text-sm">No execution data yet.</p>
      </Card>
    );
  }

  return (
    <Card className="p-5 h-full">
      <ZoneHeader title="Department execution league" sub="Worst performers first — completion rate." />
      <div className="grid grid-cols-12 gap-2 px-1.5 mb-2 text-[9.5px] uppercase tracking-wider text-on-surface-variant/40 font-semibold">
        <div className="col-span-5">Department</div>
        <div className="col-span-5">Completion</div>
        <div className="col-span-2 text-right">Proof rate</div>
      </div>
      <div className="space-y-0.5">
        {rows.map(r => (
          <button key={r.deptCode} onClick={() => onSelectDept(r.deptCode)}
            className="grid grid-cols-12 gap-2 items-center px-1.5 py-2 rounded-md hover:bg-white/4 transition w-full text-left">
            <div className="col-span-5 min-w-0">
              <div className="text-[12px] text-on-surface truncate">{r.deptName.replace(' Department', '')}</div>
              <div className="text-[10px] text-on-surface-variant/50 tabular-nums">{r.completed}/{r.assigned}</div>
            </div>
            <div className="col-span-5 flex items-center gap-2">
              <div className="flex-1">
                <ProgressBar value={r.completionPct}
                  color={r.completionPct < 35 ? 'red' : r.completionPct < 60 ? 'amber' : 'emerald'}
                  height={6} />
              </div>
              <span className="tabular-nums text-[11.5px] text-on-surface font-medium w-10 text-right">{r.completionPct}%</span>
            </div>
            <div className="col-span-2 text-right tabular-nums text-[11.5px]">
              <span style={{ color: r.proofPct < 60 && r.proofPct > 0 ? SEG.amber : '#c2c6d6' }}>
                {r.proofPct}%
              </span>
            </div>
          </button>
        ))}
      </div>
    </Card>
  );
}

function CoordinationPanel({ executions, deptRows, onSelectDept }: {
  executions: DirectiveExecution[];
  deptRows: DeptDashboardRow[];
  onSelectDept: (code: string) => void;
}) {
  const crossCases = useMemo(() => {
    const byCaseId = new Map<string, { caseId: string; caseNumber: string; depts: Map<string, { code: string; name: string; done: number; total: number; }> }>();
    executions.forEach(e => {
      if (!e.case_id) return;
      const prev = byCaseId.get(e.case_id) || { caseId: e.case_id, caseNumber: e.case_number, depts: new Map() };
      const code = e.department_code || 'UNKNOWN';
      const deptPrev = prev.depts.get(code) || { code, name: e.department_name || code, done: 0, total: 0 };
      deptPrev.total++;
      if (e.status === 'completed') deptPrev.done++;
      prev.depts.set(code, deptPrev);
      byCaseId.set(e.case_id, prev);
    });
    return [...byCaseId.values()]
      .filter(c => c.depts.size >= 2)
      .slice(0, 6);
  }, [executions]);

  if (crossCases.length === 0) {
    return (
      <Card className="p-5 h-full flex flex-col">
        <ZoneHeader title="Cross-dept coordination" sub="Multi-department case progress." />
        <div className="flex-1 flex items-center justify-center">
          <p className="text-on-surface-variant/50 text-sm">No multi-department cases.</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-5 h-full">
      <ZoneHeader title="Cross-dept coordination lag" sub="Cases stalled by a lagging department." />
      <div className="space-y-3 max-h-[360px] overflow-y-auto scrollbar-thin pr-1">
        {crossCases.map(c => (
          <div key={c.caseId}
            className="rounded-lg border border-outline-variant/20 bg-white/[0.02] px-3 py-3 hover:bg-white/[0.04] cursor-pointer transition">
            <div className="flex items-center justify-between mb-2.5">
              <div>
                <div className="text-[12px] font-medium text-on-surface">{c.caseNumber}</div>
                <div className="text-[10.5px] text-on-surface-variant/50">{c.depts.size} departments involved</div>
              </div>
              <Icon name="arrow-right" className="w-3.5 h-3.5 text-on-surface-variant/40" />
            </div>
            <div className="space-y-1.5">
              {[...c.depts.values()].map(dep => {
                const pct = dep.total > 0 ? (dep.done / dep.total) * 100 : 0;
                const isLagging = pct < 50 && dep.total > 0;
                return (
                  <div key={dep.code} className="grid grid-cols-12 items-center gap-2 text-[11px]">
                    <span className={`col-span-3 truncate font-medium`}
                      style={{ color: isLagging ? SEG.red : '#c2c6d6' }}>
                      {dep.name.replace(' Department', '')}
                    </span>
                    <div className="col-span-6">
                      <ProgressBar value={pct} color={pct >= 100 ? 'emerald' : isLagging ? 'red' : 'teal'} height={5} />
                    </div>
                    <span className="col-span-3 text-right tabular-nums text-on-surface-variant/60">
                      {dep.done}/{dep.total}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function Zone3({ execByDept, executions, deptRows, onSelectDept }: {
  execByDept: Map<string, DeptExecStats>;
  executions: DirectiveExecution[];
  deptRows: DeptDashboardRow[];
  onSelectDept: (code: string) => void;
}) {
  return (
    <section>
      <ZoneHeader title="Execution and coordination" size="section" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <LeaguePanel execByDept={execByDept} onSelectDept={onSelectDept} />
        <CoordinationPanel executions={executions} deptRows={deptRows} onSelectDept={onSelectDept} />
      </div>
    </section>
  );
}

// ── Zone 4: 30-day deadline density ──────────────────────────────────────────

interface DensityDay {
  day: number;
  count: number;
  color: 'red' | 'amber' | 'green';
  date: Date;
}

function Zone4({ deadlines, deptRows, onNavigate }: {
  deadlines: DeadlineRow[];
  deptRows: DeptDashboardRow[];
  onNavigate?: CentralLawViewProps['onNavigate'];
}) {
  const [selected, setSelected] = useState('state');
  const [hovered, setHovered] = useState<number | null>(null);

  const today = useMemo(() => {
    const d = new Date(); d.setHours(0, 0, 0, 0); return d;
  }, []);

  const densityData: DensityDay[] = useMemo(() => {
    const src = selected === 'state'
      ? deadlines
      : deadlines.filter(d => d.department_code === selected);
    const days: DensityDay[] = Array.from({ length: 30 }, (_, i) => {
      const date = new Date(today); date.setDate(today.getDate() + i);
      return { day: i + 1, count: 0, color: 'green', date };
    });
    src.forEach(dl => {
      const dt = dl.next_deadline ? new Date(dl.next_deadline) : null;
      if (!dt) return;
      dt.setHours(0, 0, 0, 0);
      const diff = Math.round((dt.getTime() - today.getTime()) / 86400000);
      if (diff >= 0 && diff < 30) days[diff].count++;
    });
    days.forEach((d, i) => {
      if (d.count > 0) {
        if (i < 3) d.color = 'red';
        else if (i < 7 && d.count > 1) d.color = 'red';
        else if (i < 14) d.color = 'amber';
        else d.color = 'green';
      }
    });
    return days;
  }, [deadlines, selected, today]);

  const max = Math.max(...densityData.map(d => d.count), 1);
  const total = densityData.reduce((a, d) => a + d.count, 0);
  const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const barColors = { red: SEG.red, amber: SEG.amber, green: SEG.emerald };

  return (
    <section>
      <ZoneHeader title="Upcoming deadlines" size="section" />
      <Card className="p-5">
        <ZoneHeader
          title="30-day deadline density"
          sub="Cases by statutory deadline date. Clusters indicate capacity emergencies."
          right={
            <div className="flex items-center gap-2">
              <label className="text-[11px] text-on-surface-variant/60 shrink-0">Scope:</label>
              <select value={selected} onChange={e => setSelected(e.target.value)}
                className="bg-surface-container-highest border border-outline-variant/30 rounded-md px-3 py-1.5 text-[12px] text-on-surface focus:outline-none focus:ring-1 focus:ring-primary-blue/50 min-w-[200px]"
                style={{ appearance: 'none', backgroundImage: `url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23c2c6d6' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polyline points='6 9 12 15 18 9'/></svg>")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 8px center', paddingRight: 24 }}>
                <option value="state">Statewide</option>
                <optgroup label="Departments">
                  {deptRows.filter(d => d.total_cases > 0).map(d =>
                    <option key={d.code} value={d.code}>{d.name}</option>
                  )}
                </optgroup>
              </select>
            </div>
          }
        />

        <div className="relative mt-1">
          <div className="absolute left-0 top-0 bottom-7 w-6 flex flex-col justify-between text-[9px] text-on-surface-variant/30 tabular-nums">
            <span>{max}</span>
            <span>{Math.round(max / 2)}</span>
            <span>0</span>
          </div>

          <div className="ml-8 flex items-end gap-[3px]" style={{ height: 180 }}>
            {densityData.map((d, i) => {
              const h = d.count === 0 ? 3 : Math.max(6, (d.count / max) * 100);
              const isHover = hovered === i;
              const bg = d.count === 0 ? 'rgba(255,255,255,0.04)' : barColors[d.color];
              return (
                <div
                  key={i}
                  onMouseEnter={() => setHovered(i)}
                  onMouseLeave={() => setHovered(null)}
                  onClick={() => d.count > 0 && onNavigate?.('deadlines')}
                  className="relative flex-1 flex items-end h-full"
                  style={{ cursor: d.count > 0 ? 'pointer' : 'default' }}
                >
                  <div className="w-full rounded-t-sm transition-all"
                    style={{ height: `${h}%`, background: bg, opacity: isHover ? 1 : 0.75 }}/>
                  {isHover && d.count > 0 && (
                    <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 z-20 pointer-events-none min-w-[140px]">
                      <div className="px-3 py-2 rounded-lg bg-surface-container-highest border border-outline-variant/30 shadow-xl text-left">
                        <div className="flex items-center justify-between mb-1">
                          <div className="tabular-nums font-semibold text-on-surface text-[12px]">
                            {d.date.getDate()} {MONTHS[d.date.getMonth()]}
                          </div>
                          <div className="text-[10px] text-on-surface-variant/50">+{i}d</div>
                        </div>
                        <div className="text-[11px] text-on-surface-variant">
                          <span className="tabular-nums font-semibold" style={{ color: bg }}>{d.count}</span>
                          {' '}case{d.count === 1 ? '' : 's'} due
                        </div>
                      </div>
                      <div className="w-2 h-2 rotate-45 bg-surface-container-highest border-r border-b border-outline-variant/30 mx-auto -mt-1"/>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="ml-8 flex justify-between mt-2 text-[9.5px] text-on-surface-variant/40">
            <span>Today</span><span>+7d</span><span>+14d</span><span>+21d</span><span>+30d</span>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-outline-variant/20 flex items-center gap-5 text-[10.5px] text-on-surface-variant/50 flex-wrap">
          <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm" style={{ background: SEG.red }}/>Critical ≤7d</span>
          <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm" style={{ background: SEG.amber }}/>Warning ≤14d</span>
          <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm" style={{ background: SEG.emerald }}/>Safe</span>
          <span className="ml-auto">
            Total in window: <span className="text-on-surface tabular-nums font-medium">{total}</span>
          </span>
          <button onClick={() => onNavigate?.('deadlines')}
            className="text-[11px] text-primary-blue hover:underline inline-flex items-center gap-1">
            Full deadline monitor <Icon name="arrow-right" className="w-3 h-3"/>
          </button>
        </div>
      </Card>
    </section>
  );
}

// ── Zone 5: 48-department grid ────────────────────────────────────────────────

function DeptTile({ dept, execStats, onSelect }: {
  dept: DeptDashboardRow;
  execStats?: DeptExecStats;
  onSelect: () => void;
}) {
  const isEmpty = dept.total_cases === 0;
  const execPct = execStats && execStats.assigned > 0
    ? Math.round((execStats.completed / execStats.assigned) * 100) : null;
  const proofPct = execStats && execStats.completed > 0
    ? Math.round((execStats.completedWithProof / execStats.completed) * 100) : null;

  if (isEmpty) {
    return (
      <div className="rounded-xl border border-dashed border-outline-variant/20 px-4 py-3.5">
        <div className="font-semibold text-[12px] text-on-surface-variant/50 truncate">{dept.name.replace(' Department', '')}</div>
        <div className="text-[9.5px] text-on-surface-variant/30 uppercase tracking-wider font-mono mt-0.5">{dept.code}</div>
        <div className="mt-2.5 text-[10.5px] text-on-surface-variant/30">No active cases</div>
      </div>
    );
  }

  return (
    <button onClick={onSelect}
      className="text-left rounded-xl bg-surface-container/60 border border-outline-variant/20 px-4 py-3.5 transition hover:bg-surface-container-high/70 hover:border-outline-variant/40 hover:shadow-lg group w-full">
      <div className="mb-1">
        <div className="flex items-start gap-1.5">
          <div className="text-[12px] font-semibold text-on-surface leading-snug min-w-0 flex-1">
            {dept.name.replace(' Department', '')}
          </div>
          <div className="flex items-center gap-1 shrink-0 -mt-0.5">
            {dept.high_risk > 0 && <PillBadge tone="red" small>{dept.high_risk} risk</PillBadge>}
          </div>
        </div>
        <div className="text-[9.5px] uppercase tracking-wider text-on-surface-variant/40 font-mono mt-0.5">{dept.code}</div>
      </div>

      <div className="mt-2.5">
        <StackedBar segments={[
          { value: dept.pending, color: 'amber' },
          { value: Math.max(0, dept.total_cases - dept.pending - dept.high_risk), color: 'teal' },
          { value: dept.high_risk, color: 'red' },
        ]} height={5} />
        <div className="mt-1.5 flex justify-between text-[10px] text-on-surface-variant/40">
          <span className="tabular-nums">{dept.total_cases} cases</span>
          <span className="tabular-nums">{dept.pending} pending</span>
        </div>
      </div>

      {execPct !== null && (
        <div className="mt-2.5 space-y-1.5">
          <div className="flex items-center gap-2 text-[10.5px]">
            <span className="text-on-surface-variant/50 w-10 shrink-0">Exec</span>
            <div className="flex-1"><ProgressBar value={execPct} color={execPct < 35 ? 'red' : execPct < 60 ? 'amber' : 'emerald'} height={4} /></div>
            <span className="tabular-nums text-on-surface w-12 text-right">{execStats!.completed}/{execStats!.assigned} · {execPct}%</span>
          </div>
          {proofPct !== null && (
            <div className="flex items-center gap-2 text-[10.5px]">
              <span className="text-on-surface-variant/50 w-10 shrink-0">Proof</span>
              <div className="flex-1"><ProgressBar value={proofPct} color={proofPct >= 75 ? 'emerald' : proofPct >= 50 ? 'amber' : 'red'} height={4} /></div>
              <span className="tabular-nums w-12 text-right" style={{ color: proofPct >= 75 ? SEG.emerald : '#c2c6d6' }}>{proofPct}%{proofPct >= 75 ? ' ✓' : ''}</span>
            </div>
          )}
        </div>
      )}
    </button>
  );
}

function SectorGroup({ sectorName, depts, execByDept, expanded, onToggle, onSelectDept }: {
  sectorName: string;
  depts: DeptDashboardRow[];
  execByDept: Map<string, DeptExecStats>;
  expanded: boolean;
  onToggle: () => void;
  onSelectDept: (code: string) => void;
}) {
  const activeCount = depts.filter(d => d.total_cases > 0).length;
  const riskCount = depts.reduce((a, d) => a + d.high_risk, 0);
  return (
    <div className="rounded-xl border border-outline-variant/15 bg-white/[0.015]">
      <button onClick={onToggle}
        className="flex items-center justify-between w-full px-4 py-3 hover:bg-white/[0.025] rounded-xl transition">
        <div className="flex items-center gap-2.5">
          <Icon name={expanded ? 'chev-down' : 'chev-right'} className="w-3.5 h-3.5 text-on-surface-variant/40" />
          <span className="text-[11.5px] font-semibold uppercase tracking-[0.12em] text-on-surface-variant/80">{sectorName}</span>
          <span className="text-[10px] text-on-surface-variant/40 tabular-nums">· {activeCount} active</span>
          {riskCount > 0 && <PillBadge tone="red" small>{riskCount} risk</PillBadge>}
        </div>
        <span className="text-[10px] text-on-surface-variant/40">{depts.length} dept{depts.length !== 1 ? 's' : ''}</span>
      </button>
      {expanded && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 p-3 pt-1.5">
          {depts.map(d => (
            <DeptTile
              key={d.code}
              dept={d}
              execStats={execByDept.get(d.code)}
              onSelect={() => onSelectDept(d.code)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function Zone5({ grouped, execByDept, onSelectDept }: {
  grouped: [string, DeptDashboardRow[]][];
  execByDept: Map<string, DeptExecStats>;
  onSelectDept: (code: string) => void;
}) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(grouped.map(([s]) => [s, false]))
  );
  const allExpanded = grouped.length > 0 && grouped.every(([s]) => expanded[s]);

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <ZoneHeader title="48 secretariat departments" size="section" />
        <button
          onClick={() => setExpanded(Object.fromEntries(grouped.map(([s]) => [s, !allExpanded])))}
          className="shrink-0 text-[11px] text-on-surface-variant/60 hover:text-on-surface px-2.5 py-1 rounded-md border border-outline-variant/30 transition">
          {allExpanded ? 'Collapse all' : 'Expand all'}
        </button>
      </div>
      <div className="space-y-2">
        {grouped.map(([sector, depts]) => (
          <SectorGroup
            key={sector}
            sectorName={sector}
            depts={[...depts].sort((a, b) => b.total_cases - a.total_cases)}
            execByDept={execByDept}
            expanded={!!expanded[sector]}
            onToggle={() => setExpanded(e => ({ ...e, [sector]: !e[sector] }))}
            onSelectDept={onSelectDept}
          />
        ))}
      </div>
    </section>
  );
}

// ── Department Detail Drawer ──────────────────────────────────────────────────

function DepartmentDrawer({ deptCode, deptRow, execStats, executions, onClose, onViewCases }: {
  deptCode: string;
  deptRow: DeptDashboardRow | undefined;
  execStats: DeptExecStats | undefined;
  executions: DirectiveExecution[];
  onClose: () => void;
  onViewCases: () => void;
}) {
  const [tab, setTab] = useState<'overview' | 'execution' | 'verify'>('overview');

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  if (!deptRow) return null;

  const deptExecs = executions.filter(e => e.department_code === deptCode);
  const execPct = execStats && execStats.assigned > 0
    ? Math.round((execStats.completed / execStats.assigned) * 100) : 0;
  const proofPct = execStats && execStats.completed > 0
    ? Math.round((execStats.completedWithProof / execStats.completed) * 100) : 0;

  const tabs = [
    { id: 'overview' as const,  label: 'Overview' },
    { id: 'execution' as const, label: 'Execution', count: execStats?.assigned },
    { id: 'verify' as const,    label: 'Verify queue', count: deptRow.pending },
  ];

  return (
    <div className="fixed inset-0 z-50 flex">
      <div onClick={onClose} className="flex-1 bg-black/60 backdrop-blur-sm" />
      <motion.aside
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ duration: 0.28, ease: [0.2, 0.7, 0.2, 1] }}
        className="w-[600px] max-w-[92vw] bg-surface-dim border-l border-outline-variant/30 shadow-2xl flex flex-col">

        <header className="px-6 py-5 border-b border-outline-variant/20 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="text-[10px] uppercase tracking-[0.18em] text-on-surface-variant/50 font-semibold">Department detail</div>
            <h2 className="text-xl font-bold tracking-tight mt-1 text-on-surface truncate">{deptRow.name}</h2>
            <div className="text-[11px] text-on-surface-variant/50 mt-0.5 font-mono uppercase tracking-wider">{deptRow.code} · {deptRow.sector}</div>
          </div>
          <button onClick={onClose}
            className="w-8 h-8 rounded-md text-on-surface-variant/60 hover:text-on-surface hover:bg-white/6 grid place-items-center transition">
            <Icon name="x" className="w-4 h-4"/>
          </button>
        </header>

        <div className="px-6 py-3 grid grid-cols-4 gap-3 border-b border-outline-variant/15">
          {[
            { l: 'Total cases', v: deptRow.total_cases, hi: false },
            { l: 'High risk',   v: deptRow.high_risk,   hi: deptRow.high_risk > 0 },
            { l: 'Pending',     v: deptRow.pending,     hi: deptRow.pending > 0 },
            { l: 'Exec %',      v: execPct + '%',       hi: false },
          ].map(s => (
            <div key={s.l}>
              <div className="text-[9.5px] uppercase tracking-wider text-on-surface-variant/40 font-semibold">{s.l}</div>
              <div className={`tabular-nums text-lg font-bold tracking-tight mt-0.5 ${s.hi ? '' : 'text-on-surface'}`}
                style={s.hi ? { color: SEG.red } : undefined}>{s.v}</div>
            </div>
          ))}
        </div>

        <div className="px-6 pt-4">
          <div className="flex gap-1">
            {tabs.map(t => (
              <button key={t.id} onClick={() => setTab(t.id)}
                className={`px-3 py-2 text-[11.5px] font-medium rounded-md transition flex items-center gap-1.5 ${tab === t.id ? 'bg-white/6 text-on-surface' : 'text-on-surface-variant/60 hover:text-on-surface'}`}>
                {t.label}
                {t.count !== undefined && <span className="tabular-nums text-[10px] text-on-surface-variant/40">({t.count})</span>}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto scrollbar-thin px-6 py-5">
          {tab === 'overview' && (
            <div className="space-y-5">
              <div className="grid grid-cols-3 gap-2">
                {[
                  { l: 'Total cases', v: deptRow.total_cases, tone: 'neutral' },
                  { l: 'High risk', v: deptRow.high_risk, tone: deptRow.high_risk > 0 ? 'red' : 'neutral' },
                  { l: 'Pending verify', v: deptRow.pending, tone: deptRow.pending > 0 ? 'amber' : 'neutral' },
                ].map(d => (
                  <div key={d.l} className="rounded-lg border border-outline-variant/20 bg-white/[0.02] p-2.5">
                    <div className="text-[10px] text-on-surface-variant/50">{d.l}</div>
                    <div className="tabular-nums text-xl font-bold tracking-tight mt-0.5"
                      style={{ color: d.tone === 'red' ? SEG.red : d.tone === 'amber' ? SEG.amber : '#e1e2ec' }}>
                      {d.v}
                    </div>
                  </div>
                ))}
              </div>
              {execStats && (
                <div className="space-y-3">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-on-surface-variant/50 font-semibold">Execution summary</div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-3 text-[12px]">
                      <span className="text-on-surface-variant/60 w-24">Completion</span>
                      <div className="flex-1"><ProgressBar value={execPct} color={execPct < 35 ? 'red' : execPct < 60 ? 'amber' : 'emerald'} height={6} /></div>
                      <span className="tabular-nums text-on-surface w-8 text-right">{execPct}%</span>
                    </div>
                    <div className="flex items-center gap-3 text-[12px]">
                      <span className="text-on-surface-variant/60 w-24">Proof rate</span>
                      <div className="flex-1"><ProgressBar value={proofPct} color={proofPct >= 75 ? 'emerald' : proofPct >= 50 ? 'amber' : 'red'} height={6} /></div>
                      <span className="tabular-nums text-on-surface w-8 text-right">{proofPct}%</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-[11px] text-center">
                    {[
                      { l: 'In Progress', v: execStats.inProgress, c: SEG.teal },
                      { l: 'Pending', v: execStats.pending, c: SEG.amber },
                      { l: 'Completed', v: execStats.completed, c: SEG.emerald },
                      { l: 'Blocked', v: execStats.blocked, c: SEG.red },
                    ].map(s => (
                      <div key={s.l} className="rounded-lg bg-white/[0.02] border border-outline-variant/15 py-2">
                        <div className="tabular-nums text-lg font-bold" style={{ color: s.c }}>{s.v}</div>
                        <div className="text-on-surface-variant/50 text-[9.5px] uppercase tracking-wider mt-0.5">{s.l}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {tab === 'execution' && (
            <div className="space-y-3">
              <div className="text-[11px] text-on-surface-variant/50">{deptExecs.length} directive{deptExecs.length !== 1 ? 's' : ''} assigned</div>
              {deptExecs.length === 0 ? (
                <p className="text-on-surface-variant/40 text-sm">No execution tasks for this department.</p>
              ) : (
                <div className="rounded-lg border border-outline-variant/20 overflow-hidden">
                  <div className="grid grid-cols-12 gap-2 px-3 py-2 bg-white/[0.03] text-[9.5px] uppercase tracking-wider text-on-surface-variant/40 font-semibold">
                    <div className="col-span-4">Case</div>
                    <div className="col-span-4">Directive</div>
                    <div className="col-span-2">Status</div>
                    <div className="col-span-2 text-right">Proof</div>
                  </div>
                  {deptExecs.map((e, i) => {
                    const tone = e.status === 'in_progress' ? 'teal' : e.status === 'completed' ? 'emerald' : e.status === 'blocked' ? 'red' : 'amber';
                    return (
                      <div key={e.id} className="grid grid-cols-12 gap-2 px-3 py-2.5 text-[11px] border-t border-outline-variant/10 items-center hover:bg-white/[0.02]">
                        <div className="col-span-4 text-on-surface-variant/70 tabular-nums truncate">{e.case_number}</div>
                        <div className="col-span-4 text-on-surface truncate">{e.govt_summary || e.directive_text?.slice(0, 50) || `Directive ${i + 1}`}</div>
                        <div className="col-span-2"><PillBadge tone={tone}>{e.status.replace('_', ' ')}</PillBadge></div>
                        <div className="col-span-2 text-right">
                          {e.proof_file
                            ? <span style={{ color: SEG.emerald }}>✓</span>
                            : e.status === 'completed'
                              ? <span style={{ color: SEG.amber }} title="No proof uploaded">!</span>
                              : <span className="text-on-surface-variant/30">—</span>}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {tab === 'verify' && (
            <div className="space-y-3">
              <div className="text-[11px] text-on-surface-variant/50">
                {deptRow.pending} case{deptRow.pending !== 1 ? 's' : ''} awaiting HLC verification.
              </div>
              {deptRow.pending === 0 ? (
                <div className="flex items-center gap-2 py-4 text-on-surface-variant/50">
                  <Icon name="check" className="w-4 h-4 text-emerald-400/60" />
                  <span className="text-sm">No cases pending verification.</span>
                </div>
              ) : (
                <div className="rounded-lg border border-outline-variant/20 p-4 text-[12px] text-on-surface-variant/60">
                  {deptRow.pending} case{deptRow.pending !== 1 ? 's' : ''} in this department
                  are awaiting HLC review. View the full case list to access the verification queue.
                </div>
              )}
            </div>
          )}
        </div>

        <footer className="px-6 py-4 border-t border-outline-variant/15 flex items-center gap-3">
          <div className="text-[11px] text-on-surface-variant/40">
            <span className="font-mono text-on-surface-variant/60">Esc</span> to close
          </div>
          <button onClick={onViewCases}
            className="ml-auto px-4 py-2.5 rounded-lg bg-primary-blue/10 border border-primary-blue/30 text-primary-blue hover:bg-primary-blue/18 font-semibold text-[12.5px] inline-flex items-center gap-2 transition">
            <Icon name="folder" className="w-4 h-4" />
            View cases for {deptRow.name.replace(' Department', '')}
            <Icon name="arrow-right" className="w-4 h-4" />
          </button>
        </footer>
      </motion.aside>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export const CentralLawView: React.FC<CentralLawViewProps> = ({
  onSelectDepartment,
  onNavigate,
}) => {
  const [deptRows, setDeptRows] = useState<DeptDashboardRow[]>([]);
  const [executions, setExecutions] = useState<DirectiveExecution[]>([]);
  const [deadlines, setDeadlines] = useState<DeadlineRow[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);
  const [drawerDept, setDrawerDept] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchByDepartmentDashboard().catch(() => [] as DeptDashboardRow[]),
      fetchExecutions().catch(() => [] as DirectiveExecution[]),
      fetchDeadlines().catch(() => [] as DeadlineRow[]),
      fetchDashboardStats().catch(() => null),
    ]).then(([depts, execs, dlns, st]) => {
      setDeptRows(depts);
      setExecutions(execs);
      setDeadlines(dlns);
      setStats(st);
    }).finally(() => setLoading(false));
  }, [refreshKey]);

  const execByDept = useMemo(() => computeExecByDept(executions), [executions]);

  const grouped = useMemo(() => {
    const m = new Map<string, DeptDashboardRow[]>();
    deptRows.forEach(r => {
      const arr = m.get(r.sector) || [];
      arr.push(r);
      m.set(r.sector, arr);
    });
    return Array.from(m.entries());
  }, [deptRows]);

  const handleSelectDept = useCallback((code: string) => {
    setDrawerDept(code);
  }, []);

  const handleViewDeptCases = useCallback(() => {
    if (drawerDept) {
      setDrawerDept(null);
      onSelectDepartment(drawerDept);
    }
  }, [drawerDept, onSelectDepartment]);

  const now = new Date();
  const fmt = now.toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

  if (loading) {
    return (
      <div className="py-10 flex items-center justify-center h-64">
        <span className="material-symbols-outlined text-4xl animate-spin text-primary-blue opacity-40">progress_activity</span>
      </div>
    );
  }

  const totalOverdue = deadlines.filter(d => d.urgency === 'overdue').length;
  const slaBreach = stats?.pending_review ?? 0;

  return (
    <div className="py-6 pb-20 space-y-8 max-w-[1440px] mx-auto">

      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <div className="text-[10.5px] uppercase tracking-[0.22em] text-on-surface-variant/50 font-semibold">
            Central Law Department · State Monitoring
          </div>
          <h1 className="mt-2 text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-on-surface">
            Statewide compliance, at a glance.
          </h1>
          <p className="mt-2 text-[13px] text-on-surface-variant/60 max-w-xl">
            System health, departmental execution, and statutory deadlines across {deptRows.length} secretariat departments.
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <div className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-lg border border-outline-variant/20 bg-surface-container/50 text-[11px] text-on-surface-variant/60">
            <Icon name="clock" className="w-3.5 h-3.5"/> {fmt}
          </div>
          <button onClick={() => setRefreshKey(k => k + 1)}
            className="px-3 py-2 rounded-lg border border-outline-variant/20 bg-surface-container/50 hover:bg-surface-container-high/70 text-[11.5px] text-on-surface-variant inline-flex items-center gap-1.5 transition">
            <Icon name="reload" className="w-3.5 h-3.5"/> Refresh
          </button>
        </div>
      </div>

      {/* Alert banner */}
      {(totalOverdue > 0 || slaBreach > 0) && (
        <div className="rounded-xl border border-error-red/20 bg-error-red/5 px-4 py-3 flex items-center gap-3">
          <span className="w-7 h-7 rounded-md bg-error-red/10 border border-error-red/25 grid place-items-center" style={{ color: SEG.red }}>
            <Icon name="alert" className="w-3.5 h-3.5"/>
          </span>
          <div className="text-[12px] text-on-surface">
            {totalOverdue > 0 && (
              <><span className="font-semibold">{totalOverdue} case{totalOverdue !== 1 ? 's' : ''} breached statutory deadlines</span>
              <span className="text-on-surface-variant/60"> with zero or partial execution. </span></>
            )}
            {slaBreach > 0 && (
              <span className="text-on-surface-variant/70">{slaBreach} case{slaBreach !== 1 ? 's' : ''} pending HLC verification.</span>
            )}
          </div>
          <button onClick={() => onNavigate?.('deadlines')}
            className="ml-auto text-[11px] inline-flex items-center gap-1 transition hover:underline" style={{ color: SEG.red }}>
            Jump to deadlines <Icon name="arrow-right" className="w-3 h-3"/>
          </button>
        </div>
      )}

      <Zone1
        stats={stats}
        executions={executions}
        deadlines={deadlines}
        onNavigate={onNavigate}
      />

      <Zone2
        deptRows={deptRows}
        deadlines={deadlines}
        onSelectDept={handleSelectDept}
      />

      <Zone3
        execByDept={execByDept}
        executions={executions}
        deptRows={deptRows}
        onSelectDept={handleSelectDept}
      />

      <Zone4
        deadlines={deadlines}
        deptRows={deptRows}
        onNavigate={onNavigate}
      />

      <Zone5
        grouped={grouped}
        execByDept={execByDept}
        onSelectDept={handleSelectDept}
      />

      <AnimatePresence>
        {drawerDept && (
          <DepartmentDrawer
            deptCode={drawerDept}
            deptRow={deptRows.find(d => d.code === drawerDept)}
            execStats={execByDept.get(drawerDept)}
            executions={executions}
            onClose={() => setDrawerDept(null)}
            onViewCases={handleViewDeptCases}
          />
        )}
      </AnimatePresence>
    </div>
  );
};
