import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { fetchCases, CaseData } from '../api/client';
import { shortPartyTitle } from '../utils/truncate';

const StatCard = ({ icon, label, value, trend, trendColor, iconBg }: any) => (
  <div className="glass-card p-6 flex flex-col gap-4 glass-card-hover group">
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
      <h3 className="text-4xl font-bold text-on-surface mt-1 tracking-tight">{value}</h3>
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

export const Dashboard = ({ onSelectCase }: { onSelectCase: (id: string) => void }) => {
  const [cases, setCases] = useState<CaseData[]>([]);
  const [loading, setLoading] = useState(true);

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

  // Build a simple 30-day heatmap from real deadlines
  const today = new Date();
  const heatmapCells = Array.from({ length: 30 }).map((_, i) => {
    const day = i + 1;
    const targetDate = new Date(today);
    targetDate.setDate(today.getDate() + day);
    const dateStr = targetDate.toISOString().split('T')[0];

    // Count how many cases have a deadline on this day
    const matchingCases = cases.filter(c => {
      const ap = c.judgments?.[0]?.action_plan;
      if (!ap) return false;
      const d = ap.compliance_deadline || ap.statutory_appeal_deadline;
      return d === dateStr;
    });

    const count = matchingCases.length;
    let bgColor = 'bg-surface-container-highest/20 border-outline-variant/10 text-on-surface-variant opacity-40';
    let caseId: string | null = null;

    if (count >= 3) {
      bgColor = 'bg-error-red/30 border-error-red/30 text-on-surface opacity-100 cursor-pointer hover:bg-error-red/50';
      caseId = matchingCases[0]?.id;
    } else if (count === 2) {
      bgColor = 'bg-primary-blue text-on-primary-blue border-primary-blue opacity-100 cursor-pointer hover:bg-primary-blue/90';
      caseId = matchingCases[0]?.id;
    } else if (count === 1) {
      bgColor = 'bg-primary-blue/30 border-primary-blue/30 text-on-surface opacity-100 cursor-pointer hover:bg-primary-blue/50';
      caseId = matchingCases[0]?.id;
    }

    return { day, bgColor, caseId };
  });

  if (loading) {
    return (
      <div className="py-10 flex items-center justify-center h-64">
        <span className="material-symbols-outlined text-4xl animate-spin text-primary-blue opacity-40">progress_activity</span>
      </div>
    );
  }

  return (
    <div className="py-10 space-y-8 max-w-[1440px] mx-auto">
      {/* Header */}
      <div className="space-y-1">
        <h2 className="text-5xl font-bold text-on-surface tracking-tighter">System Dashboard</h2>
        <p className="text-on-surface-variant text-lg font-medium opacity-70">
          Monitoring <span className="text-on-surface">{totalCases}</span> active cases across judicial circuits.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
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
        {/* Heatmap Section */}
        <div className="lg:col-span-8 glass-card p-8">
          <div className="flex justify-between items-center mb-10">
            <div>
              <h4 className="text-3xl font-bold text-on-surface tracking-tight">Deadline Heatmap</h4>
              <p className="text-on-surface-variant text-sm font-medium mt-1">Next 30 days — case filing urgency distribution.</p>
            </div>
            <div className="flex items-center gap-1.5 opacity-40">
              <div className="w-3.5 h-3.5 rounded bg-surface-container-highest"></div>
              <div className="w-3.5 h-3.5 rounded bg-primary-blue/20"></div>
              <div className="w-3.5 h-3.5 rounded bg-primary-blue/60"></div>
              <div className="w-3.5 h-3.5 rounded bg-primary-blue"></div>
            </div>
          </div>
          
          <div className="grid grid-cols-5 sm:grid-cols-10 gap-4">
            {heatmapCells.map((cell, i) => (
              <div 
                key={i}
                onClick={() => cell.caseId && onSelectCase(cell.caseId)}
                className={`aspect-square rounded-xl border flex items-center justify-center text-sm font-bold transition-all ${cell.bgColor}`}
              >
                {cell.day.toString().padStart(2, '0')}
              </div>
            ))}
          </div>
        </div>

        {/* Risk Board */}
        <div className="lg:col-span-4 glass-card p-8 flex flex-col">
          <h4 className="text-2xl font-bold text-on-surface tracking-tight mb-8">Risk Board</h4>
          <div className="space-y-4 flex-grow">
            {riskBoard.length > 0 ? riskBoard.map(c => {
              const risk = caseRisk(c);
              const days = daysUntilDeadline(c);
              return (
                <div 
                  key={c.id} 
                  onClick={() => onSelectCase(c.id)}
                  className="bg-surface-dim/40 border border-outline-variant/20 rounded-2xl p-4 hover:bg-surface-container-high transition-colors cursor-pointer group"
                >
                  <div className="flex justify-between items-start mb-3">
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
                  <h5 className="text-on-surface font-bold text-lg tracking-tight group-hover:text-primary-blue transition-colors">
                    {shortPartyTitle(c.petitioner_name, c.respondent_name)}
                  </h5>
                  <p className="text-on-surface-variant text-[10px] font-bold uppercase tracking-widest mt-1 opacity-70">
                    {c.case_number} • {c.court_name}
                  </p>
                </div>
              );
            }) : (
              <div className="flex flex-col items-center justify-center text-center p-10 opacity-50">
                <span className="material-symbols-outlined text-4xl mb-3">verified_user</span>
                <p className="font-bold text-on-surface-variant">No high-risk cases</p>
                <p className="text-sm text-on-surface-variant">All cases are at low risk currently.</p>
              </div>
            )}
          </div>
          <button 
            onClick={() => onSelectCase('')}
            className="w-full mt-8 py-3 text-primary-blue font-bold text-xs uppercase tracking-widest border border-primary-blue/20 rounded-xl hover:bg-primary-blue/5 transition-all"
          >
            View All Cases
          </button>
        </div>

        {/* Recent Cases */}
        <div className="lg:col-span-12 glass-card p-8">
          <div className="flex justify-between items-center mb-8">
            <h4 className="text-2xl font-bold text-on-surface tracking-tight">Recent Cases</h4>
            <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest opacity-60">
              Last {Math.min(cases.length, 5)} of {totalCases}
            </span>
          </div>
          
          {/* Table Header */}
          <div className="grid grid-cols-12 gap-4 pb-4 border-b border-outline-variant/20 text-on-surface-variant text-[10px] font-bold uppercase tracking-[0.15em]">
            <div className="col-span-4">Case</div>
            <div className="col-span-2">Court</div>
            <div className="col-span-2">Risk</div>
            <div className="col-span-2">Status</div>
            <div className="col-span-2 text-right">Date</div>
          </div>
          
          {/* Table Rows */}
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
                className="grid grid-cols-12 gap-4 py-4 border-b border-outline-variant/10 items-center hover:bg-white/[0.02] -mx-4 px-4 transition-colors cursor-pointer group"
              >
                <div className="col-span-4 min-w-0">
                  <p className="font-bold text-on-surface text-sm truncate group-hover:text-primary-blue transition-colors">
                    {shortPartyTitle(c.petitioner_name, c.respondent_name)}
                  </p>
                  <p className="text-on-surface-variant text-[10px] font-medium truncate">{c.case_number}</p>
                </div>
                <div className="col-span-2 text-on-surface-variant text-xs font-medium truncate">{c.court_name}</div>
                <div className="col-span-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                    risk === 'High' ? 'bg-error-red/10 text-error-red' :
                    risk === 'Medium' ? 'bg-tertiary-container/10 text-tertiary-container' :
                    'bg-green-500/10 text-green-400'
                  }`}>
                    {risk}
                  </span>
                </div>
                <div className="col-span-2">
                  <span className={`text-[10px] font-bold uppercase tracking-wider ${
                    c.status === 'pending' ? 'text-amber-400' : 'text-green-400'
                  }`}>
                    {c.status}
                  </span>
                </div>
                <div className="col-span-2 text-right text-on-surface-variant text-xs font-medium">{dateStr}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
