import { motion } from 'framer-motion';
import { Calendar, AlertTriangle, Clock } from 'lucide-react';
import { formatDate, daysUntil, cn } from '@/lib/utils';

interface DeadlineCardProps {
  title: string;
  deadline: string;
  basis?: string;
}

export default function DeadlineCard({ title, deadline, basis }: DeadlineCardProps) {
  const days = daysUntil(deadline);
  const urgency = days <= 7 ? 'red' : days <= 14 ? 'amber' : 'green';
  const colors = {
    red: { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400' },
    amber: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-400' },
    green: { bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-400' },
  };
  const c = colors[urgency];

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={cn('glass-card p-5 border', c.border)}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wide">{title}</p>
          <p className="mt-1 text-lg font-bold text-white">{formatDate(deadline)}</p>
          {basis && <p className="mt-1 text-xs text-slate-400">{basis}</p>}
        </div>
        <div className={cn('rounded-xl p-3', c.bg)}>
          {urgency === 'red' ? <AlertTriangle size={20} className={c.text} /> : <Calendar size={20} className={c.text} />}
        </div>
      </div>
      <div className={cn('mt-3 flex items-center gap-1.5 text-sm font-medium', c.text)}>
        <Clock size={14} />
        {days > 0 ? `${days} days remaining` : days === 0 ? 'Due today!' : `${Math.abs(days)} days overdue!`}
      </div>
    </motion.div>
  );
}
