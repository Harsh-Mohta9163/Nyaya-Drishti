import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'motion/react';
import { DeptDashboardRow, fetchByDepartmentDashboard } from '../api/client';

interface CentralLawViewProps {
  onSelectDepartment: (deptCode: string) => void;
}

/**
 * Central Law Department / State Monitoring dashboard.
 * Renders a sector-grouped grid of all 48 departments with case counts.
 * Clicking a card invokes onSelectDepartment(code) — App.tsx then navigates
 * to the case list filtered by ?department=<code>.
 */
export const CentralLawView: React.FC<CentralLawViewProps> = ({ onSelectDepartment }) => {
  const [rows, setRows] = useState<DeptDashboardRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchByDepartmentDashboard()
      .then(setRows)
      .catch(err => console.error('by-department fetch failed:', err))
      .finally(() => setLoading(false));
  }, []);

  // Group by sector for visual organization
  const grouped = useMemo(() => {
    const m = new Map<string, DeptDashboardRow[]>();
    rows.forEach(r => {
      const arr = m.get(r.sector) || [];
      arr.push(r);
      m.set(r.sector, arr);
    });
    return Array.from(m.entries());
  }, [rows]);

  const totalCases = rows.reduce((s, r) => s + r.total_cases, 0);
  const totalHighRisk = rows.reduce((s, r) => s + r.high_risk, 0);
  const totalPending = rows.reduce((s, r) => s + r.pending, 0);
  const activeDepts = rows.filter(r => r.total_cases > 0).length;

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
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-on-surface tracking-tighter">Central Law Dashboard</h2>
        <p className="text-on-surface-variant text-base sm:text-lg font-medium opacity-70">
          Aggregated litigation view across <span className="text-on-surface">{rows.length}</span> Karnataka secretariat departments.
        </p>
      </div>

      {/* Aggregate stat strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
        <div className="glass-card p-4 sm:p-6">
          <p className="text-on-surface-variant text-[10px] font-bold uppercase tracking-widest opacity-60">Total Cases (Statewide)</p>
          <h3 className="text-3xl sm:text-4xl font-bold text-on-surface mt-2 tracking-tight">{totalCases}</h3>
        </div>
        <div className="glass-card p-4 sm:p-6">
          <p className="text-on-surface-variant text-[10px] font-bold uppercase tracking-widest opacity-60">Active Departments</p>
          <h3 className="text-3xl sm:text-4xl font-bold text-on-surface mt-2 tracking-tight">{activeDepts}<span className="text-base text-on-surface-variant font-medium"> / {rows.length}</span></h3>
        </div>
        <div className="glass-card p-4 sm:p-6">
          <p className="text-on-surface-variant text-[10px] font-bold uppercase tracking-widest opacity-60">High Risk</p>
          <h3 className="text-3xl sm:text-4xl font-bold text-error-red mt-2 tracking-tight">{totalHighRisk}</h3>
        </div>
        <div className="glass-card p-4 sm:p-6">
          <p className="text-on-surface-variant text-[10px] font-bold uppercase tracking-widest opacity-60">Pending Review</p>
          <h3 className="text-3xl sm:text-4xl font-bold text-on-surface mt-2 tracking-tight">{totalPending}</h3>
        </div>
      </div>

      {/* Sector groups */}
      {grouped.map(([sector, depts]) => (
        <section key={sector} className="space-y-3">
          <div className="flex items-baseline justify-between">
            <h3 className="text-sm sm:text-base font-bold text-primary-blue tracking-tight uppercase">
              {sector}
            </h3>
            <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant opacity-60">
              {depts.length} dept{depts.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
            {depts.map((d, i) => {
              const hasCases = d.total_cases > 0;
              const hasRisk = d.high_risk > 0;
              return (
                <motion.button
                  key={d.code}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.02 }}
                  onClick={() => onSelectDepartment(d.code)}
                  className={`glass-card glass-card-hover text-left p-4 sm:p-5 flex flex-col gap-3 group ${
                    !hasCases ? 'opacity-60' : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <h4 className="text-on-surface font-bold text-sm sm:text-base tracking-tight line-clamp-2 group-hover:text-primary-blue transition-colors">
                        {d.name}
                      </h4>
                      <p className="text-on-surface-variant text-[10px] font-medium uppercase tracking-widest opacity-50 mt-1">
                        {d.code}
                      </p>
                    </div>
                    <span className="material-symbols-outlined text-primary-blue/70 text-xl shrink-0 group-hover:text-primary-blue transition-colors">
                      arrow_forward
                    </span>
                  </div>
                  <div className="flex items-center gap-4 pt-2 border-t border-outline-variant/20">
                    <div className="flex flex-col">
                      <span className="text-[9px] font-bold text-on-surface-variant uppercase tracking-widest opacity-50">Total</span>
                      <span className="text-on-surface font-bold text-lg tracking-tight">{d.total_cases}</span>
                    </div>
                    <div className="flex flex-col">
                      <span className="text-[9px] font-bold text-on-surface-variant uppercase tracking-widest opacity-50">High Risk</span>
                      <span className={`font-bold text-lg tracking-tight ${hasRisk ? 'text-error-red' : 'text-on-surface-variant'}`}>
                        {d.high_risk}
                      </span>
                    </div>
                    <div className="flex flex-col">
                      <span className="text-[9px] font-bold text-on-surface-variant uppercase tracking-widest opacity-50">Pending</span>
                      <span className="text-on-surface font-bold text-lg tracking-tight">{d.pending}</span>
                    </div>
                  </div>
                </motion.button>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
};
