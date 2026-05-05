import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { FileText, ClipboardCheck, AlertTriangle, Calendar, CheckCircle, Gauge } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import StatCard from '@/components/dashboard/StatCard';
import DeadlineHeatmap from '@/components/dashboard/DeadlineHeatmap';
import RiskBoard from '@/components/dashboard/RiskBoard';
import AppealCountdown from '@/components/dashboard/AppealCountdown';
import { useDashboardStats, useDeadlines, useHighRiskCases } from '@/hooks/useDashboard';
import { usePendingReviews } from '@/hooks/useReviews';
import { useNavigate } from 'react-router-dom';
import { cn, riskColor } from '@/lib/utils';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import LoadingSpinner from '@/components/common/LoadingSpinner';

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

export default function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();

  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: deadlines = [], isLoading: deadlinesLoading } = useDeadlines(30);
  const { data: highRisk = [], isLoading: highRiskLoading } = useHighRiskCases();
  const { data: pendingReviews = [] } = usePendingReviews();

  if (statsLoading) {
    return <div className="flex items-center justify-center h-64"><LoadingSpinner /></div>;
  }

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      <motion.div variants={item}>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">{t('dashboard.title')}</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Welcome back, <span className="font-medium text-foreground">{user?.username}</span>. Here's your overview.
        </p>
      </motion.div>

      {/* Stat Cards */}
      <motion.div variants={item} className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title={t('dashboard.totalCases')} value={stats?.total_cases ?? 0} icon={FileText} color="blue" />
        <StatCard title={t('dashboard.pendingReview')} value={stats?.pending_review ?? 0} icon={ClipboardCheck} color="amber" />
        <StatCard title={t('dashboard.highRisk')} value={stats?.high_risk ?? 0} icon={AlertTriangle} color="red" />
        <StatCard title={t('dashboard.upcomingDeadlines')} value={stats?.upcoming_deadlines_7d ?? 0} icon={Calendar} color="green" />
      </motion.div>

      {/* Additional stat row */}
      <motion.div variants={item} className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <StatCard title={t('dashboard.verifiedThisMonth')} value={stats?.verified_this_month ?? 0} icon={CheckCircle} color="green" />
        <StatCard title={t('dashboard.avgConfidence')} value={Math.round((stats?.avg_extraction_confidence ?? 0) * 100)} icon={Gauge} color="blue" trend={{ value: 2.3, label: 'vs last month' }} />
      </motion.div>

      {/* Deadline Heatmap + Risk Board */}
      <motion.div variants={item} className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <DeadlineHeatmap deadlines={deadlines} onCellClick={(id) => navigate(`/cases/${id}`)} />
        <RiskBoard cases={highRisk} />
      </motion.div>

      {/* Role-specific widgets */}
      {user?.role === 'reviewer' && pendingReviews.length > 0 && (
        <motion.div variants={item}>
          <Card className="border-border bg-card shadow-sm">
            <CardHeader className="pb-3 border-b border-border/50">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <ClipboardCheck size={16} className="text-blue-500" />
                {t('dashboard.verificationQueue')}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="flex flex-col divide-y divide-border/50">
                {pendingReviews.map((r, i) => (
                  <motion.div
                    key={r.case_id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.08 }}
                    onClick={() => navigate(`/cases/${r.case_id}/review`)}
                    className="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-muted/30 transition-colors group"
                  >
                    <div>
                      <p className="text-sm font-semibold text-foreground group-hover:text-blue-400 transition-colors">{r.case_number}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{r.court}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={cn('rounded-full px-2 py-0.5 text-[10px] font-bold tracking-wide uppercase', riskColor[r.contempt_risk])}>
                        {r.contempt_risk}
                      </span>
                      <span className="text-xs text-muted-foreground capitalize">{r.review_level}</span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {user?.role === 'legal_advisor' && (
        <motion.div variants={item}>
          <AppealCountdown deadlines={deadlines} />
        </motion.div>
      )}
    </motion.div>
  );
}
