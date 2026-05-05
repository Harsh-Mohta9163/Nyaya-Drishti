import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, CheckCircle, AlertTriangle, Shield } from 'lucide-react';
import GlassCard from '@/components/common/GlassCard';
import ConfidenceBadge from '@/components/common/ConfidenceBadge';
import ActionTimeline from '@/components/action-plan/ActionTimeline';
import DeadlineCard from '@/components/action-plan/DeadlineCard';
import CCMSStageMap from '@/components/action-plan/CCMSStageMap';
import SimilarCases from '@/components/action-plan/SimilarCases';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { cn, riskColor } from '@/lib/utils';
import { useCaseDetail } from '@/hooks/useCases';
import { useActionPlan } from '@/hooks/useActionPlan';
import { api } from '@/lib/api';

const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.08 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

export default function ActionPlanPage() {
  const { id } = useParams();
  const caseId = Number(id);
  const navigate = useNavigate();
  const { t } = useTranslation();
  
  const { data: caseData, isLoading: caseLoading } = useCaseDetail(caseId);
  const { data: serverPlan, isLoading: planLoading } = useActionPlan(caseId);
  
  const [plan, setPlan] = useState(serverPlan);

  // Sync state when server data loads
  useEffect(() => {
    if (serverPlan) {
      setPlan(serverPlan);
    }
  }, [serverPlan]);

  const toggleComplete = (actionId: string) => {
    if (!plan) return;
    setPlan(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        compliance_actions: prev.compliance_actions.map((a: any) =>
          a.id === actionId ? { ...a, is_complete: !a.is_complete } : a
        ),
      };
    });
  };

  if (caseLoading || planLoading) {
    return <div className="flex items-center justify-center h-64"><LoadingSpinner /></div>;
  }

  if (!caseData || !plan) {
    return (
      <div className="space-y-6">
        <button onClick={() => navigate(`/cases/${id}`)} className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors">
          <ArrowLeft size={16} /> Back to Case
        </button>
        <div className="flex flex-col items-center justify-center h-64 glass-card p-8">
          <Shield size={48} className="text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-slate-300">Action Plan not generated yet</h3>
          <p className="text-sm text-slate-500 mb-6 text-center max-w-sm">
            Generate an actionable compliance plan based on the extracted court directives.
          </p>
          <button
            onClick={async () => {
              try {
                await api.post(`/api/cases/${id}/action-plan/`);
                window.location.reload();
              } catch (e) {
                console.error('Failed to generate action plan', e);
              }
            }}
            className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-blue-600 to-blue-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-blue-500/25 hover:from-blue-500 hover:to-blue-400 transition-all"
          >
            Generate Action Plan
          </button>
        </div>
      </div>
    );
  }

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
                {plan.recommendation_reasoning && (
                  <p className="text-sm text-slate-400 mt-1 max-w-2xl">{plan.recommendation_reasoning}</p>
                )}
              </div>
            </div>
            {plan.recommendation_confidence && <ConfidenceBadge value={plan.recommendation_confidence} label={t('caseDetail.confidence')} />}
          </div>
        </div>
      </motion.div>

      {/* Deadlines */}
      <motion.div variants={item} className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <DeadlineCard
          title={t('actionPlan.legalDeadline')}
          deadline={plan.legal_deadline || ''}
          basis={plan.statutory_basis}
        />
        <DeadlineCard
          title={t('actionPlan.internalDeadline')}
          deadline={plan.internal_deadline || ''}
        />
      </motion.div>

      {/* CCMS Stage Map */}
      <motion.div variants={item}>
        <CCMSStageMap currentStage={plan.ccms_stage} recommendation={plan.recommendation} />
      </motion.div>

      {/* Compliance Actions */}
      {plan.compliance_actions && plan.compliance_actions.length > 0 && (
        <motion.div variants={item}>
          <GlassCard>
            <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
              <Shield size={16} className="text-blue-400" />
              {t('actionPlan.complianceSteps')}
            </h3>
            <ActionTimeline actions={plan.compliance_actions} onToggleComplete={toggleComplete} />
          </GlassCard>
        </motion.div>
      )}

      {/* Responsible Departments */}
      {plan.responsible_departments && plan.responsible_departments.length > 0 && (
        <motion.div variants={item}>
          <GlassCard>
            <h3 className="text-sm font-semibold text-slate-200 mb-3">{t('actionPlan.responsibleDepts')}</h3>
            <div className="flex flex-wrap gap-2">
              {plan.responsible_departments.map((dept: string) => (
                <span key={dept} className="rounded-full bg-blue-500/10 border border-blue-500/20 px-3 py-1 text-xs font-medium text-blue-300">
                  {dept}
                </span>
              ))}
            </div>
          </GlassCard>
        </motion.div>
      )}

      {/* Similar Cases RAG */}
      {plan.similar_cases && plan.similar_cases.length > 0 && (
        <motion.div variants={item}>
          <SimilarCases cases={plan.similar_cases} recommendation={plan.recommendation} />
        </motion.div>
      )}
    </motion.div>
  );
}
