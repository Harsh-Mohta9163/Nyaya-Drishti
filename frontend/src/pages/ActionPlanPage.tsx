import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, CheckCircle, AlertTriangle, Shield } from 'lucide-react';
import { mockActionPlan, mockCases } from '@/lib/mockData';
import GlassCard from '@/components/common/GlassCard';
import ConfidenceBadge from '@/components/common/ConfidenceBadge';
import ActionTimeline from '@/components/action-plan/ActionTimeline';
import DeadlineCard from '@/components/action-plan/DeadlineCard';
import CCMSStageMap from '@/components/action-plan/CCMSStageMap';
import SimilarCases from '@/components/action-plan/SimilarCases';
import { cn, riskColor } from '@/lib/utils';

const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.08 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

export default function ActionPlanPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [plan, setPlan] = useState(mockActionPlan);
  const caseData = mockCases.find(c => c.id === Number(id)) || mockCases[0];

  const toggleComplete = (actionId: string) => {
    setPlan(prev => ({
      ...prev,
      compliance_actions: prev.compliance_actions.map(a =>
        a.id === actionId ? { ...a, is_complete: !a.is_complete } : a
      ),
    }));
  };

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-8">
      {/* Header */}
      <motion.div variants={item}>
        <button onClick={() => navigate(`/cases/${id}`)} className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors mb-4">
          <ArrowLeft size={16} /> Back to Case
        </button>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">{t('actionPlan.title')}</h1>
            <p className="text-sm text-slate-400 mt-1">{caseData.case_number} • {caseData.court}</p>
          </div>
          <span className={cn('rounded-full border px-3 py-1 text-xs font-medium', riskColor[plan.contempt_risk])}>
            {plan.contempt_risk} Risk
          </span>
        </div>
      </motion.div>

      {/* Recommendation Banner */}
      <motion.div variants={item}>
        <div className={cn(
          'glass-card p-8 border-l-4',
          plan.recommendation === 'Comply'
            ? 'border-l-green-500'
            : 'border-l-amber-500'
        )}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={cn(
                'flex h-14 w-14 items-center justify-center rounded-2xl',
                plan.recommendation === 'Comply' ? 'bg-green-500/10' : 'bg-amber-500/10'
              )}>
                {plan.recommendation === 'Comply'
                  ? <CheckCircle size={28} className="text-green-400" />
                  : <AlertTriangle size={28} className="text-amber-400" />
                }
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide">{t('actionPlan.recommendation')}</p>
                <p className={cn(
                  'text-2xl font-bold',
                  plan.recommendation === 'Comply' ? 'text-green-400' : 'text-amber-400'
                )}>
                  {plan.recommendation === 'Comply' ? t('actionPlan.comply') : t('actionPlan.appeal')}
                </p>
              </div>
            </div>
            <ConfidenceBadge value={plan.recommendation_confidence} label={t('caseDetail.confidence')} />
          </div>
        </div>
      </motion.div>

      {/* Deadlines */}
      <motion.div variants={item} className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <DeadlineCard
          title={t('actionPlan.legalDeadline')}
          deadline={plan.legal_deadline}
          basis={plan.statutory_basis}
        />
        <DeadlineCard
          title={t('actionPlan.internalDeadline')}
          deadline={plan.internal_deadline}
        />
      </motion.div>

      {/* CCMS Stage Map */}
      <motion.div variants={item}>
        <CCMSStageMap currentStage={plan.ccms_stage} recommendation={plan.recommendation} />
      </motion.div>

      {/* Compliance Actions */}
      <motion.div variants={item}>
        <GlassCard>
          <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
            <Shield size={16} className="text-blue-400" />
            {t('actionPlan.complianceSteps')}
          </h3>
          <ActionTimeline actions={plan.compliance_actions} onToggleComplete={toggleComplete} />
        </GlassCard>
      </motion.div>

      {/* Responsible Departments */}
      <motion.div variants={item}>
        <GlassCard>
          <h3 className="text-sm font-semibold text-slate-200 mb-3">{t('actionPlan.responsibleDepts')}</h3>
          <div className="flex flex-wrap gap-2">
            {plan.responsible_departments.map(dept => (
              <span key={dept} className="rounded-full bg-blue-500/10 border border-blue-500/20 px-3 py-1 text-xs font-medium text-blue-300">
                {dept}
              </span>
            ))}
          </div>
        </GlassCard>
      </motion.div>

      {/* Similar Cases RAG */}
      <motion.div variants={item}>
        <SimilarCases cases={plan.similar_cases} recommendation={plan.recommendation} />
      </motion.div>
    </motion.div>
  );
}
