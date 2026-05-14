import React, { useEffect, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { fetchCases, CaseData } from '../api/client';
import { shortPartyTitle } from '../utils/truncate';
import { useAuth, isGlobalRole } from '../context/AuthContext';

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

const StatCard = ({ icon, label, value, trend, trendColor, iconBg }: any) => (
  <div className="glass-card p-4 sm:p-6 flex flex-col gap-3 sm:gap-4 glass-card-hover group">
    <div className="flex justify-between items-start">
      <div className={`p-2 rounded-lg flex items-center justify-center ${iconBg}`}>
        <span className="material-symbols-outlined text-xl">{icon}</span>
      </div>
      {trend && (
        <span className={`text-[10px] font-bold uppercase tracking-wider ${trendColor}`}>
          {trend}
        </span>
      )}
    </div>
    <div>
      <p className="text-on-surface-variant text-[10px] font-bold uppercase tracking-widest opacity-60">{label}</p>
      <h3 className="text-3xl sm:text-4xl font-bold text-on-surface mt-1 tracking-tight">{value}</h3>
    </div>
  </div>
);

/** Derive risk level from a case + its first judgment */
function caseRisk(c: CaseData): 'High' | 'Medium' | 'Low' {
  const j = c.judgments?.[0];
  if (!j) return 'Low';
  const risk = (j.contempt_risk || '').toLowerCase();
  if (risk === 'high') return 'High';
  if (risk === 'medium') return 'Medium';
  return 'Low';
}

/** Compute days remaining until a deadline-like field */
function daysUntilDeadline(c: CaseData): number | null {
  const ap = c.judgments?.[0]?.action_plan;
  if (!ap) return null;
  const deadline = ap.compliance_deadline || ap.statutory_appeal_deadline || ap.internal_compliance_deadline;
  if (!deadline) return null;
  const diff = Math.ceil((new Date(deadline).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
  return diff;
}

/** Collect all deadline dates from a case (YYYY-MM-DD strings) */
function getCaseDeadlineDates(c: CaseData): string[] {
  const j = c.judgments?.[0];
  const ap = j?.action_plan;
  const dateSet = new Set<string>();

  // 1. DB-level deadline fields on the action_plan
  if (ap) {
    if (ap.compliance_deadline) dateSet.add(ap.compliance_deadline);
    if (ap.statutory_appeal_deadline) dateSet.add(ap.statutory_appeal_deadline);
    if (ap.internal_compliance_deadline) dateSet.add(ap.internal_compliance_deadline);
    if (ap.internal_appeal_deadline) dateSet.add(ap.internal_appeal_deadline);
    if ((ap as any).legal_deadline) dateSet.add((ap as any).legal_deadline);

    // 2. RAG recommendation verdict — this is where most deadlines actually live
    const rec = ap.full_rag_recommendation;
    if (rec && typeof rec === 'object') {
      const verdict = rec.verdict;
      if (verdict && typeof verdict === 'object') {
        // limitation_deadline is typically "YYYY-MM-DD"
        if (verdict.limitation_deadline) dateSet.add(verdict.limitation_deadline);
      }
    }
  }

  // 3. Fallback: use date_of_order so the case at least appears on the calendar
  if (dateSet.size === 0 && j?.date_of_order) {
    const orderDate = j.date_of_order.split('T')[0]; // handle ISO datetime
    dateSet.add(orderDate);
  }

  return [...dateSet];
}

/** Format a date as YYYY-MM-DD in local time */
function toLocalDateStr(d: Date): string {
  const y = d.getFullYear();
  const m = (d.getMonth() + 1).toString().padStart(2, '0');
  const day = d.getDate().toString().padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export const Dashboard = ({ onSelectCase }: { onSelectCase: (id: string) => void }) => {
  const { user } = useAuth();
  const [cases, setCases] = useState<CaseData[]>([]);
  const [loading, setLoading] = useState(true);
  const [calendarMonth, setCalendarMonth] = useState(() => {
    const now = new Date();
    return { year: now.getFullYear(), month: now.getMonth() };
  });
  const [showPicker, setShowPicker] = useState(false);
  const [pickerYear, setPickerYear] = useState(() => new Date().getFullYear());

  useEffect(() => {
    fetchCases()
      .then(data => setCases(data))
      .catch(err => console.error('Dashboard fetch failed:', err))
      .finally(() => setLoading(false));
  }, []);

  // Derive stats from real data
  const totalCases = cases.length;
  const pendingReview = cases.filter(c => c.status === 'pending').length;
  const highRiskCases = cases.filter(c => caseRisk(c) === 'High');
  const highRiskCount = highRiskCases.length;

  // Cases with upcoming deadlines in the next 7 days
  const upcomingDeadlines = cases.filter(c => {
    const d = daysUntilDeadline(c);
    return d !== null && d >= 0 && d <= 7;
  });

  // Cases with any action plan analysis completed
  const analyzedCases = cases.filter(c => c.judgments?.[0]?.action_plan?.full_rag_recommendation);

  // Build the risk board — top priority cases (high/medium risk, sorted by urgency)
  const riskBoard = [...cases]
    .filter(c => caseRisk(c) !== 'Low')
    .sort((a, b) => {
      const da = daysUntilDeadline(a) ?? 999;
      const db = daysUntilDeadline(b) ?? 999;
      return da - db;
    })
    .slice(0, 5);

  // Build deadline lookup: dateStr -> { cases, count }
  const deadlineMap = useMemo(() => {
    const map = new Map<string, { cases: CaseData[], count: number }>();
    cases.forEach(c => {
      const dates = getCaseDeadlineDates(c);
      dates.forEach(dateStr => {
        const existing = map.get(dateStr);
        if (existing) {
          existing.cases.push(c);
          existing.count += 1;
        } else {
          map.set(dateStr, { cases: [c], count: 1 });
        }
      });
    });
    return map;
  }, [cases]);

  // Calendar grid for the selected month
  const calendarGrid = useMemo(() => {
    const { year, month } = calendarMonth;
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startPad = firstDay.getDay(); // 0=Sun
    const daysInMonth = lastDay.getDate();
    const todayStr = toLocalDateStr(new Date());

    const cells: Array<{
      day: number | null;
      dateStr: string;
      isToday: boolean;
      isPast: boolean;
      count: number;
      caseId: string | null;
      risk: 'High' | 'Medium' | 'Low' | null;
    }> = [];

    // Padding cells for start of month
    for (let i = 0; i < startPad; i++) {
      cells.push({ day: null, dateStr: '', isToday: false, isPast: false, count: 0, caseId: null, risk: null });
    }

    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${year}-${(month + 1).toString().padStart(2, '0')}-${d.toString().padStart(2, '0')}`;
      const entry = deadlineMap.get(dateStr);
      const count = entry?.count || 0;
      const firstCase = entry?.cases?.[0] || null;
      const risk = firstCase ? caseRisk(firstCase) : null;
      const isPast = dateStr < todayStr;
      const isToday = dateStr === todayStr;

      cells.push({
        day: d,
        dateStr,
        isToday,
        isPast,
        count,
        caseId: firstCase?.id || null,
        risk,
      });
    }

    return cells;
  }, [calendarMonth, deadlineMap]);

  // Count deadlines in current viewed month
  const monthDeadlineCount = calendarGrid.filter(c => c.count > 0).length;

  const goToPrevMonth = () => {
    setCalendarMonth(prev => {
      const m = prev.month - 1;
      return m < 0 ? { year: prev.year - 1, month: 11 } : { year: prev.year, month: m };
    });
  };

  const goToNextMonth = () => {
    setCalendarMonth(prev => {
      const m = prev.month + 1;
      return m > 11 ? { year: prev.year + 1, month: 0 } : { year: prev.year, month: m };
    });
  };

  const goToToday = () => {
    const now = new Date();
    setCalendarMonth({ year: now.getFullYear(), month: now.getMonth() });
  };

  if (loading) {
    return (
      <div className="py-10 flex items-center justify-center h-64">
        <span className="material-symbols-outlined text-4xl animate-spin text-primary-blue opacity-40">progress_activity</span>
      </div>
    );
  }

  return (
    <div className="py-6 sm:py-10 space-y-6 sm:space-y-8 max-w-[1440px] mx-auto">
      {/* Header */}
      <div className="space-y-1">
        <div className="flex items-baseline gap-3 flex-wrap">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-on-surface tracking-tighter">System Dashboard</h2>
          {user?.department_name && (
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-primary-blue/15 text-primary-blue border border-primary-blue/30 tracking-tight">
              {user.department_name}
            </span>
          )}
          {isGlobalRole(user?.role) && (
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-primary-blue/15 text-primary-blue border border-primary-blue/30 tracking-tight uppercase">
              All Departments
            </span>
          )}
        </div>
        <p className="text-on-surface-variant text-base sm:text-lg font-medium opacity-70">
          Monitoring <span className="text-on-surface">{totalCases}</span> active cases
          {user?.department_name ? ` assigned to ${user.department_name}` : ' across judicial circuits'}.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
        <StatCard 
          icon="folder_managed" 
          label="Total Cases" 
          value={totalCases} 
          trend={analyzedCases.length > 0 ? `${analyzedCases.length} Analyzed` : undefined} 
          trendColor="text-primary-blue"
          iconBg="bg-primary-blue/10 text-primary-blue"
        />
        <StatCard 
          icon="visibility" 
          label="Pending Review" 
          value={pendingReview} 
          iconBg="bg-tertiary-container/10 text-tertiary-container"
        />
        <StatCard 
          icon="warning" 
          label="High Risk Cases" 
          value={highRiskCount} 
          trend={highRiskCount > 0 ? "Critical" : undefined} 
          trendColor="text-error-red"
          iconBg="bg-error-red/10 text-error-red"
        />
        <StatCard 
          icon="calendar_month" 
          label="Deadlines" 
          value={upcomingDeadlines.length} 
          trend="Next 7 Days" 
          trendColor="text-on-surface-variant"
          iconBg="bg-surface-container-highest text-on-surface-variant"
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Calendar Section */}
        <div className="lg:col-span-8 glass-card p-4 sm:p-6">
          {/* Calendar Header — compact row */}
          <div className="flex items-center justify-between mb-4 gap-2">
            <div className="min-w-0">
              <h4 className="text-lg sm:text-xl font-bold text-on-surface tracking-tight">Deadline Calendar</h4>
              <p className="text-on-surface-variant text-[10px] sm:text-xs font-medium mt-0.5 opacity-70">
                {monthDeadlineCount > 0
                  ? `${monthDeadlineCount} day${monthDeadlineCount > 1 ? 's' : ''} with deadlines`
                  : 'No deadlines this month'}
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {/* Legend — desktop only */}
              <div className="hidden lg:flex items-center gap-2.5 mr-2 text-[8px] font-bold uppercase tracking-widest text-on-surface-variant opacity-50">
                <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-sm bg-amber-400/40"></div>Past</div>
                <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-sm bg-primary-blue/40"></div>Upcoming</div>
                <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-sm bg-error-red/40"></div>Urgent</div>
              </div>
              <button
                onClick={goToToday}
                className="px-2 py-1 text-[9px] font-bold uppercase tracking-widest text-primary-blue border border-primary-blue/20 rounded-md hover:bg-primary-blue/10 transition-colors"
              >
                Today
              </button>
            </div>
          </div>

          {/* Month Navigator — compact with picker toggle */}
          <div className="flex items-center justify-between mb-3 relative">
            <button
              onClick={goToPrevMonth}
              className="p-1.5 rounded-lg hover:bg-surface-container-high transition-colors"
            >
              <span className="material-symbols-outlined text-on-surface-variant text-lg">chevron_left</span>
            </button>
            <button
              onClick={() => { setShowPicker(p => !p); setPickerYear(calendarMonth.year); }}
              className="text-sm sm:text-base font-bold text-on-surface tracking-tight hover:text-primary-blue transition-colors flex items-center gap-1.5 px-2 py-1 rounded-lg hover:bg-primary-blue/5"
            >
              {MONTH_NAMES[calendarMonth.month]} {calendarMonth.year}
              <span className="material-symbols-outlined text-sm opacity-50">{showPicker ? 'expand_less' : 'expand_more'}</span>
            </button>
            <button
              onClick={goToNextMonth}
              className="p-1.5 rounded-lg hover:bg-surface-container-high transition-colors"
            >
              <span className="material-symbols-outlined text-on-surface-variant text-lg">chevron_right</span>
            </button>

            {/* Month/Year Picker Dropdown */}
            {showPicker && (
              <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-50 bg-surface-container border border-outline-variant/30 rounded-xl shadow-2xl p-4 w-[280px] sm:w-[300px]">
                {/* Year selector */}
                <div className="flex items-center justify-between mb-3">
                  <button
                    onClick={() => setPickerYear(y => y - 1)}
                    className="p-1 rounded hover:bg-surface-container-high transition-colors"
                  >
                    <span className="material-symbols-outlined text-on-surface-variant text-base">chevron_left</span>
                  </button>
                  <span className="text-sm font-bold text-on-surface">{pickerYear}</span>
                  <button
                    onClick={() => setPickerYear(y => y + 1)}
                    className="p-1 rounded hover:bg-surface-container-high transition-colors"
                  >
                    <span className="material-symbols-outlined text-on-surface-variant text-base">chevron_right</span>
                  </button>
                </div>
                {/* Month grid */}
                <div className="grid grid-cols-3 gap-1.5">
                  {MONTH_NAMES.map((mn, mi) => {
                    const isSelected = calendarMonth.month === mi && calendarMonth.year === pickerYear;
                    const isCurrent = new Date().getMonth() === mi && new Date().getFullYear() === pickerYear;
                    return (
                      <button
                        key={mi}
                        onClick={() => {
                          setCalendarMonth({ year: pickerYear, month: mi });
                          setShowPicker(false);
                        }}
                        className={`py-1.5 px-1 rounded-lg text-[11px] font-bold uppercase tracking-wider transition-all ${
                          isSelected
                            ? 'bg-primary-blue text-on-primary-blue'
                            : isCurrent
                            ? 'bg-primary-blue/10 text-primary-blue border border-primary-blue/30'
                            : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
                        }`}
                      >
                        {mn.slice(0, 3)}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Weekday Headers */}
          <div className="grid grid-cols-7 gap-1 mb-1">
            {WEEKDAYS.map(wd => (
              <div key={wd} className="text-center text-[9px] sm:text-[10px] font-bold text-on-surface-variant uppercase tracking-widest opacity-40 py-1">
                {wd}
              </div>
            ))}
          </div>

          {/* Calendar Grid — compact fixed-height cells */}
          <div className="grid grid-cols-7 gap-1">
            {calendarGrid.map((cell, i) => {
              if (cell.day === null) {
                return <div key={`pad-${i}`} className="h-9 sm:h-10" />;
              }

              const hasDeadline = cell.count > 0;
              const isOverdue = hasDeadline && cell.isPast;

              let cellClasses = 'h-9 sm:h-10 rounded-md border flex flex-col items-center justify-center text-[11px] sm:text-xs font-bold transition-all ';

              if (cell.isToday) {
                cellClasses += hasDeadline
                  ? 'bg-primary-blue text-on-primary-blue border-primary-blue ring-1 ring-primary-blue/40 cursor-pointer hover:scale-105 '
                  : 'bg-primary-blue/10 text-primary-blue border-primary-blue/40 ';
              } else if (isOverdue) {
                cellClasses += cell.count >= 3
                  ? 'bg-error-red/25 border-error-red/30 text-error-red cursor-pointer hover:bg-error-red/40 '
                  : 'bg-amber-400/15 border-amber-400/25 text-amber-400 cursor-pointer hover:bg-amber-400/25 ';
              } else if (hasDeadline) {
                cellClasses += cell.count >= 3
                  ? 'bg-error-red/20 border-error-red/25 text-on-surface cursor-pointer hover:bg-error-red/35 '
                  : cell.count >= 2
                  ? 'bg-primary-blue/40 border-primary-blue/40 text-on-surface cursor-pointer hover:bg-primary-blue/55 '
                  : 'bg-primary-blue/20 border-primary-blue/25 text-on-surface cursor-pointer hover:bg-primary-blue/35 ';
              } else if (cell.isPast) {
                cellClasses += 'bg-surface-container-highest/10 border-outline-variant/5 text-on-surface-variant opacity-30 ';
              } else {
                cellClasses += 'bg-surface-container-highest/20 border-outline-variant/10 text-on-surface-variant opacity-50 hover:opacity-70 ';
              }

              return (
                <div
                  key={cell.dateStr}
                  onClick={() => cell.caseId && onSelectCase(cell.caseId)}
                  className={cellClasses}
                  title={hasDeadline ? `${cell.count} deadline${cell.count > 1 ? 's' : ''} on ${cell.dateStr}` : undefined}
                >
                  {cell.day}
                  {hasDeadline && (
                    <div className="flex items-center gap-px mt-px">
                      {Array.from({ length: Math.min(cell.count, 3) }).map((_, di) => (
                        <div
                          key={di}
                          className={`w-1 h-1 rounded-full ${
                            isOverdue ? 'bg-amber-400' :
                            cell.isToday ? 'bg-white' :
                            cell.count >= 3 ? 'bg-error-red' : 'bg-primary-blue'
                          }`}
                        />
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Risk Board */}
        <div className="lg:col-span-4 glass-card p-5 sm:p-8 flex flex-col">
          <h4 className="text-xl sm:text-2xl font-bold text-on-surface tracking-tight mb-6 sm:mb-8">Risk Board</h4>
          <div className="space-y-3 sm:space-y-4 flex-grow">
            {riskBoard.length > 0 ? riskBoard.map(c => {
              const risk = caseRisk(c);
              const days = daysUntilDeadline(c);
              return (
                <div 
                  key={c.id} 
                  onClick={() => onSelectCase(c.id)}
                  className="bg-surface-dim/40 border border-outline-variant/20 rounded-xl sm:rounded-2xl p-3 sm:p-4 hover:bg-surface-container-high transition-colors cursor-pointer group"
                >
                  <div className="flex justify-between items-start mb-2 sm:mb-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-widest ${
                      risk === 'High' ? 'bg-error-red/10 text-error-red' : 'bg-tertiary-container/10 text-tertiary-container'
                    }`}>
                      {risk} Risk
                    </span>
                    {days !== null && (
                      <div className={`flex items-center gap-1.5 text-xs font-bold ${
                        risk === 'High' ? 'text-error-red' : 'text-on-surface-variant'
                      }`}>
                        <span className="material-symbols-outlined text-sm">schedule</span>
                        {days}d
                      </div>
                    )}
                  </div>
                  <h5 className="text-on-surface font-bold text-base sm:text-lg tracking-tight group-hover:text-primary-blue transition-colors line-clamp-1">
                    {shortPartyTitle(c.petitioner_name, c.respondent_name)}
                  </h5>
                  <p className="text-on-surface-variant text-[10px] font-bold uppercase tracking-widest mt-1 opacity-70 truncate">
                    {c.case_number} • {c.court_name}
                  </p>
                </div>
              );
            }) : (
              <div className="flex flex-col items-center justify-center text-center p-6 sm:p-10 opacity-50">
                <span className="material-symbols-outlined text-4xl mb-3">verified_user</span>
                <p className="font-bold text-on-surface-variant">No high-risk cases</p>
                <p className="text-sm text-on-surface-variant">All cases are at low risk currently.</p>
              </div>
            )}
          </div>
          <button 
            onClick={() => onSelectCase('')}
            className="w-full mt-6 sm:mt-8 py-3 text-primary-blue font-bold text-xs uppercase tracking-widest border border-primary-blue/20 rounded-xl hover:bg-primary-blue/5 transition-all"
          >
            View All Cases
          </button>
        </div>

        {/* Recent Cases */}
        <div className="lg:col-span-12 glass-card p-5 sm:p-8">
          <div className="flex justify-between items-center mb-6 sm:mb-8">
            <h4 className="text-xl sm:text-2xl font-bold text-on-surface tracking-tight">Recent Cases</h4>
            <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest opacity-60">
              Last {Math.min(cases.length, 5)} of {totalCases}
            </span>
          </div>
          
          {/* Desktop Table Header — hidden on mobile */}
          <div className="hidden md:grid grid-cols-12 gap-4 pb-4 border-b border-outline-variant/20 text-on-surface-variant text-[10px] font-bold uppercase tracking-[0.15em]">
            <div className="col-span-4">Case</div>
            <div className="col-span-2">Court</div>
            <div className="col-span-2">Risk</div>
            <div className="col-span-2">Status</div>
            <div className="col-span-2 text-right">Date</div>
          </div>
          
          {/* Table Rows — card layout on mobile, grid on desktop */}
          {cases.slice(0, 5).map(c => {
            const risk = caseRisk(c);
            const j = c.judgments?.[0];
            const dateStr = j?.date_of_order
              ? new Date(j.date_of_order).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
              : '—';
            return (
              <div 
                key={c.id}
                onClick={() => onSelectCase(c.id)}
                className="md:grid md:grid-cols-12 md:gap-4 py-4 border-b border-outline-variant/10 items-center hover:bg-white/[0.02] md:-mx-4 md:px-4 transition-colors cursor-pointer group"
              >
                {/* Mobile: stacked layout */}
                <div className="md:col-span-4 min-w-0">
                  <p className="font-bold text-on-surface text-sm truncate group-hover:text-primary-blue transition-colors">
                    {shortPartyTitle(c.petitioner_name, c.respondent_name)}
                  </p>
                  <p className="text-on-surface-variant text-[10px] font-medium truncate">{c.case_number}</p>
                </div>
                <div className="md:col-span-2 text-on-surface-variant text-xs font-medium truncate hidden md:block">{c.court_name}</div>
                <div className="flex items-center gap-2 mt-2 md:mt-0 md:contents">
                  <div className="md:col-span-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                      risk === 'High' ? 'bg-error-red/10 text-error-red' :
                      risk === 'Medium' ? 'bg-tertiary-container/10 text-tertiary-container' :
                      'bg-green-500/10 text-green-400'
                    }`}>
                      {risk}
                    </span>
                  </div>
                  <div className="md:col-span-2">
                    <span className={`text-[10px] font-bold uppercase tracking-wider ${
                      c.status === 'pending' ? 'text-amber-400' : 'text-green-400'
                    }`}>
                      {c.status}
                    </span>
                  </div>
                  <div className="md:col-span-2 text-right text-on-surface-variant text-xs font-medium ml-auto md:ml-0">{dateStr}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
