import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

interface ProcessingStatusProps {
  status: string;
}

const stages = ['uploaded', 'processing', 'extracted', 'review_pending'];

export default function ProcessingStatus({ status }: ProcessingStatusProps) {
  const currentIndex = stages.indexOf(status);

  return (
    <div className="glass-card p-6">
      <div className="flex items-center gap-2 mb-6">
        <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>
          <Loader2 size={18} className="text-blue-400" />
        </motion.div>
        <h3 className="text-sm font-semibold text-slate-200">Processing Judgment...</h3>
      </div>

      <div className="flex items-center justify-between">
        {stages.map((stage, i) => (
          <div key={stage} className="flex items-center flex-1">
            <div className="flex flex-col items-center">
              <div className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold transition-all ${
                i <= currentIndex
                  ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30'
                  : 'bg-slate-800 text-slate-500'
              }`}>
                {i + 1}
              </div>
              <span className={`mt-2 text-[10px] font-medium ${
                i <= currentIndex ? 'text-blue-400' : 'text-slate-600'
              }`}>
                {stage.replace('_', ' ')}
              </span>
            </div>
            {i < stages.length - 1 && (
              <div className={`h-0.5 flex-1 mx-2 rounded ${
                i < currentIndex ? 'bg-blue-500' : 'bg-slate-800'
              }`} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
