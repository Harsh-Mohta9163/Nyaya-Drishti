import { motion } from 'framer-motion';
import { BookOpen, ExternalLink } from 'lucide-react';
import type { SimilarCase } from '@/types';
import { useTranslation } from 'react-i18next';

interface SimilarCasesProps {
  cases: SimilarCase[];
  recommendation?: string;
}

export default function SimilarCases({ cases, recommendation }: SimilarCasesProps) {
  const { t } = useTranslation();
  const complianceCount = cases.filter(c => c.outcome.toLowerCase().includes('compli')).length;

  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BookOpen size={16} className="text-purple-400" />
          <h3 className="text-sm font-semibold text-slate-200">{t('actionPlan.similarCases')}</h3>
        </div>
        {recommendation && (
          <span className="text-xs text-slate-400">
            ({complianceCount} of {cases.length} similar cases → {recommendation.toLowerCase()} recommended)
          </span>
        )}
      </div>

      <div className="space-y-3">
        {cases.map((c, i) => (
          <motion.div
            key={c.case_number}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            className="rounded-lg bg-slate-800/30 border border-slate-700/50 p-4"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-blue-400">{c.case_number}</span>
                  <span className="rounded-full bg-purple-500/10 px-2 py-0.5 text-[10px] font-medium text-purple-300">
                    {Math.round(c.similarity_score * 100)}% match
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-400">{t('actionPlan.outcome')}: {c.outcome}</p>
                <p className="mt-2 text-xs text-slate-500 leading-relaxed">{c.summary}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
