import React from 'react';
import { motion } from 'motion/react';

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

export const Dashboard = ({ onSelectCase }: { onSelectCase: (id: string) => void }) => {
  // Mock data for the dashboard
  const stats = {
    total_cases: 124,
    pending_review: 12,
    high_risk: 5,
    upcoming_deadlines_7d: 8
  };

  const highRiskCases = [
    { id: 'ND-2023-SP-882', risk: 'High', days: 4, petitioner: 'ABC Industries', court: 'SC Delhi' },
    { id: 'SLP/4567/2024', risk: 'Medium', days: 12, petitioner: 'Ramaiah & Sons', court: 'Karnataka HC' },
    { id: 'HC-2023-14', risk: 'High', days: 2, petitioner: 'Global Tech', court: 'Bombay HC' }
  ];

  // Generate heatmap cells (30 days)
  const heatmapCells = Array.from({ length: 30 }).map((_, i) => {
    const day = i + 1;
    // Map colors based on provided screenshot
    let bgColor = 'bg-surface-container-highest/20 border-outline-variant/10 text-on-surface-variant opacity-40';
    let isClickable = false;
    
    if ([1, 5, 7, 14, 15, 24, 27].includes(day)) {
      bgColor = 'bg-primary-blue/30 border-primary-blue/30 text-on-surface opacity-100 cursor-pointer hover:bg-primary-blue/50';
      isClickable = true;
    }
    if ([3, 18].includes(day)) {
      bgColor = 'bg-primary-blue text-on-primary-blue border-primary-blue opacity-100 cursor-pointer hover:bg-primary-blue/90';
      isClickable = true;
    }
    if ([12].includes(day)) {
      bgColor = 'bg-tertiary-container/30 border-tertiary-container/30 text-on-surface opacity-100 cursor-pointer hover:bg-tertiary-container/50';
      isClickable = true;
    }
    if ([15].includes(day)) {
      bgColor = 'bg-error-red/20 border-error-red/30 text-on-surface opacity-100 cursor-pointer hover:bg-error-red/40';
      isClickable = true;
    }

    return { day, bgColor, isClickable };
  });

  return (
    <div className="py-10 space-y-8 max-w-[1440px] mx-auto">
      {/* Header */}
      <div className="space-y-1">
        <h2 className="text-5xl font-bold text-on-surface tracking-tighter">System Dashboard</h2>
        <p className="text-on-surface-variant text-lg font-medium opacity-70">
          Analyzing active legal parameters across judicial circuits for <span className="text-on-surface">Adv. Sarah Jenkins</span>.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          icon="folder_managed" 
          label="Total Cases" 
          value={stats.total_cases} 
          trend="+12% vs LY" 
          trendColor="text-primary-blue"
          iconBg="bg-primary-blue/10 text-primary-blue"
        />
        <StatCard 
          icon="visibility" 
          label="Pending Review" 
          value={stats.pending_review} 
          iconBg="bg-tertiary-container/10 text-tertiary-container"
        />
        <StatCard 
          icon="warning" 
          label="High Risk Cases" 
          value={stats.high_risk} 
          trend="Critical" 
          trendColor="text-error-red"
          iconBg="bg-error-red/10 text-error-red"
        />
        <StatCard 
          icon="calendar_month" 
          label="Deadlines" 
          value={stats.upcoming_deadlines_7d} 
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
              <p className="text-on-surface-variant text-sm font-medium mt-1">Temporal distribution of case filing urgency.</p>
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
                onClick={() => cell.isClickable && onSelectCase('HC-2023-14')}
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
            {highRiskCases.map(c => (
              <div 
                key={c.id} 
                onClick={() => onSelectCase(c.id)}
                className="bg-surface-dim/40 border border-outline-variant/20 rounded-2xl p-4 hover:bg-surface-container-high transition-colors cursor-pointer group"
              >
                <div className="flex justify-between items-start mb-3">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-widest ${
                    c.risk === 'High' ? 'bg-error-red/10 text-error-red' : 'bg-tertiary-container/10 text-tertiary-container'
                  }`}>
                    {c.risk} Risk
                  </span>
                  <div className={`flex items-center gap-1.5 text-xs font-bold ${
                    c.risk === 'High' ? 'text-error-red' : 'text-on-surface-variant'
                  }`}>
                    <span className="material-symbols-outlined text-sm">schedule</span>
                    {c.days}d
                  </div>
                </div>
                <h5 className="text-on-surface font-bold text-lg tracking-tight group-hover:text-primary-blue transition-colors">
                  {c.id}
                </h5>
                <p className="text-on-surface-variant text-[10px] font-bold uppercase tracking-widest mt-1 opacity-70">
                  {c.petitioner} • {c.court}
                </p>
              </div>
            ))}
          </div>
          <button className="w-full mt-8 py-3 text-primary-blue font-bold text-xs uppercase tracking-widest border border-primary-blue/20 rounded-xl hover:bg-primary-blue/5 transition-all">
            View All Risk Alerts
          </button>
        </div>
      </div>
    </div>
  );
};
