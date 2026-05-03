import { useState } from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import {
  LineChart, Line, PieChart, Pie, Cell, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { cn } from '@/lib/utils';
import GlassCard from '@/components/common/GlassCard';

const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.08 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

// Mock analytics data
const casesOverTime = [
  { month: 'Jan', cases: 8 }, { month: 'Feb', cases: 12 }, { month: 'Mar', cases: 15 },
  { month: 'Apr', cases: 11 }, { month: 'May', cases: 18 }, { month: 'Jun', cases: 22 },
  { month: 'Jul', cases: 14 }, { month: 'Aug', cases: 19 }, { month: 'Sep', cases: 16 },
  { month: 'Oct', cases: 20 }, { month: 'Nov', cases: 25 }, { month: 'Dec', cases: 17 },
];

const riskDistribution = [
  { name: 'High', value: 8, color: '#ef4444' },
  { name: 'Medium', value: 15, color: '#f59e0b' },
  { name: 'Low', value: 19, color: '#22c55e' },
];

const deptWorkload = [
  { dept: 'Revenue', active: 18 }, { dept: 'Finance', active: 12 },
  { dept: 'Education', active: 8 }, { dept: 'Agriculture', active: 6 },
  { dept: 'Health', active: 10 }, { dept: 'Law', active: 14 },
];

const extractionConfidence = [
  { month: 'Jan', confidence: 0.85 }, { month: 'Feb', confidence: 0.87 },
  { month: 'Mar', confidence: 0.89 }, { month: 'Apr', confidence: 0.88 },
  { month: 'May', confidence: 0.91 }, { month: 'Jun', confidence: 0.90 },
  { month: 'Jul', confidence: 0.92 }, { month: 'Aug', confidence: 0.93 },
  { month: 'Sep', confidence: 0.91 }, { month: 'Oct', confidence: 0.94 },
  { month: 'Nov', confidence: 0.93 }, { month: 'Dec', confidence: 0.95 },
];

const statusFunnel = [
  { status: 'Uploaded', count: 142 }, { status: 'Processing', count: 12 },
  { status: 'Extracted', count: 98 }, { status: 'Review Pending', count: 23 },
  { status: 'Verified', count: 67 }, { status: 'Action Created', count: 45 },
];

const appealVsComply = [
  { name: 'Comply', value: 108, color: '#22c55e' },
  { name: 'Appeal', value: 34, color: '#f59e0b' },
];

type DateRange = '30d' | '90d' | '12m';

const tooltipStyle = {
  contentStyle: { backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', fontSize: '12px' },
  labelStyle: { color: '#94a3b8' },
};

export default function AnalyticsPage() {
  const { t } = useTranslation();
  const [dateRange, setDateRange] = useState<DateRange>('12m');

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      <motion.div variants={item} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">{t('analytics.title')}</h1>
          <p className="text-sm text-slate-400 mt-1">Comprehensive overview of case analytics</p>
        </div>
        <div className="flex gap-1 rounded-lg bg-slate-800/50 p-1">
          {(['30d', '90d', '12m'] as DateRange[]).map(r => (
            <button
              key={r}
              onClick={() => setDateRange(r)}
              className={cn(
                'rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
                dateRange === r ? 'bg-blue-500/20 text-blue-400' : 'text-slate-500 hover:text-slate-300'
              )}
            >
              {t(`analytics.last${r === '30d' ? '30d' : r === '90d' ? '90d' : '12m'}`)}
            </button>
          ))}
        </div>
      </motion.div>

      {/* Row 1: Cases Over Time + Risk Distribution */}
      <motion.div variants={item} className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <GlassCard>
          <h3 className="text-sm font-semibold text-slate-200 mb-4">{t('analytics.casesOverTime')}</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={casesOverTime}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip {...tooltipStyle} />
              <Line type="monotone" dataKey="cases" stroke="#3b82f6" strokeWidth={2} dot={{ fill: '#3b82f6', r: 3 }} activeDot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        </GlassCard>

        <GlassCard>
          <h3 className="text-sm font-semibold text-slate-200 mb-4">{t('analytics.riskDistribution')}</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={riskDistribution} cx="50%" cy="50%" innerRadius={55} outerRadius={90} dataKey="value" stroke="none">
                {riskDistribution.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip {...tooltipStyle} />
              <Legend
                formatter={(value) => <span className="text-xs text-slate-400">{value}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        </GlassCard>
      </motion.div>

      {/* Row 2: Department Workload + Extraction Confidence */}
      <motion.div variants={item} className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <GlassCard>
          <h3 className="text-sm font-semibold text-slate-200 mb-4">{t('analytics.deptWorkload')}</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={deptWorkload}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="dept" stroke="#64748b" fontSize={10} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="active" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </GlassCard>

        <GlassCard>
          <h3 className="text-sm font-semibold text-slate-200 mb-4">{t('analytics.extractionConfidence')}</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={extractionConfidence}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} domain={[0.8, 1]} tickFormatter={(v: number) => `${Math.round(v * 100)}%`} />
              <Tooltip {...tooltipStyle} formatter={(value: any) => `${Math.round(value * 100)}%`} />
              <defs>
                <linearGradient id="confGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <Area type="monotone" dataKey="confidence" stroke="#22c55e" fill="url(#confGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </GlassCard>
      </motion.div>

      {/* Row 3: Status Funnel + Appeal vs Comply */}
      <motion.div variants={item} className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <GlassCard>
          <h3 className="text-sm font-semibold text-slate-200 mb-4">{t('analytics.statusFunnel')}</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={statusFunnel} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis type="number" stroke="#64748b" fontSize={11} />
              <YAxis type="category" dataKey="status" stroke="#64748b" fontSize={10} width={100} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </GlassCard>

        <GlassCard>
          <h3 className="text-sm font-semibold text-slate-200 mb-4">{t('analytics.appealVsComply')}</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={appealVsComply} cx="50%" cy="50%" innerRadius={55} outerRadius={90} dataKey="value" stroke="none">
                {appealVsComply.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip {...tooltipStyle} />
              <Legend formatter={(value) => <span className="text-xs text-slate-400">{value}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </GlassCard>
      </motion.div>
    </motion.div>
  );
}
