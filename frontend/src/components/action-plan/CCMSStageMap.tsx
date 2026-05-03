import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import type { Recommendation } from '@/types';

interface CCMSStageMapProps {
  currentStage: string;
  recommendation: Recommendation;
}

const stages = [
  'LCO Proposal',
  'GA/LCO Authorization',
  'Draft PWR',
  'Approved PWR',
  'Draft SO from Advocate',
  'Affidavit Filing',
  'Order Compliance Stage',
];

const finalStages = {
  Comply: 'Closed / Complied',
  Appeal: 'Proposed for Appeal',
};

export default function CCMSStageMap({ currentStage, recommendation }: CCMSStageMapProps) {
  const currentIndex = stages.findIndex(s => currentStage.includes(s) || s.includes(currentStage));

  return (
    <div className="glass-card p-5">
      <h3 className="text-sm font-semibold text-slate-200 mb-5">CCMS Workflow Stage</h3>
      <div className="flex flex-wrap items-center gap-2">
        {stages.map((stage, i) => (
          <div key={stage} className="flex items-center">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: i * 0.06 }}
              className={cn(
                'rounded-lg px-3 py-2 text-xs font-medium border transition-all',
                i < currentIndex
                  ? 'bg-green-500/10 border-green-500/30 text-green-400'
                  : i === currentIndex
                    ? 'bg-blue-500/20 border-blue-500/50 text-blue-300 shadow-lg shadow-blue-500/10'
                    : 'bg-slate-800/30 border-slate-700/50 text-slate-500'
              )}
            >
              {stage}
            </motion.div>
            {i < stages.length - 1 && (
              <div className={cn('w-4 h-0.5 mx-1', i < currentIndex ? 'bg-green-500/30' : 'bg-slate-700')} />
            )}
          </div>
        ))}
        <div className="w-4 h-0.5 mx-1 bg-slate-700" />
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: stages.length * 0.06 }}
          className={cn(
            'rounded-lg px-3 py-2 text-xs font-medium border',
            recommendation === 'Comply'
              ? 'bg-green-500/10 border-green-500/30 text-green-400'
              : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
          )}
        >
          {finalStages[recommendation]}
        </motion.div>
      </div>
    </div>
  );
}
