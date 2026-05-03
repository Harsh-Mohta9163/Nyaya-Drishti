import { motion } from 'framer-motion';
import { Check, Circle, ArrowDown } from 'lucide-react';
import type { ComplianceAction } from '@/types';
import { cn } from '@/lib/utils';

interface ActionTimelineProps {
  actions: ComplianceAction[];
  onToggleComplete?: (id: string) => void;
}

export default function ActionTimeline({ actions, onToggleComplete }: ActionTimelineProps) {
  return (
    <div className="space-y-0">
      {actions.map((action, i) => (
        <motion.div
          key={action.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.1 }}
          className="relative flex gap-4"
        >
          {/* Timeline line */}
          <div className="flex flex-col items-center">
            <button
              onClick={() => onToggleComplete?.(action.id)}
              className={cn(
                'z-10 flex h-8 w-8 items-center justify-center rounded-full border-2 transition-all',
                action.is_complete
                  ? 'border-green-500 bg-green-500/20 text-green-400'
                  : 'border-slate-600 bg-slate-800 text-slate-500 hover:border-blue-500'
              )}
            >
              {action.is_complete ? <Check size={14} /> : <Circle size={14} />}
            </button>
            {i < actions.length - 1 && (
              <div className={cn('w-0.5 flex-1 min-h-[40px]', action.is_complete ? 'bg-green-500/30' : 'bg-slate-700')} />
            )}
          </div>

          {/* Content */}
          <div className={cn('flex-1 pb-6', action.depends_on.length > 0 && !actions.find(a => a.id === action.depends_on[0])?.is_complete && 'opacity-50')}>
            <div className="glass-card p-4">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs text-slate-500">Step {action.step_number}</span>
                  <p className={cn('text-sm font-medium mt-0.5', action.is_complete ? 'text-green-400 line-through' : 'text-slate-200')}>
                    {action.action}
                  </p>
                </div>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <span className="rounded-md bg-purple-500/10 border border-purple-500/20 px-2 py-0.5 text-xs text-purple-300">
                  {action.responsible_department}
                </span>
                {action.depends_on.length > 0 && (
                  <span className="flex items-center gap-1 text-[10px] text-slate-500">
                    <ArrowDown size={10} /> Depends on Step {actions.find(a => a.id === action.depends_on[0])?.step_number}
                  </span>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
