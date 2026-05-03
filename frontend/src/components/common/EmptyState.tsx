import { motion } from 'framer-motion';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
}

export default function EmptyState({ title = 'No data available', description, icon }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex flex-col items-center justify-center py-16 text-center"
    >
      <div className="mb-4 rounded-full bg-slate-800/50 p-4">
        {icon || <Inbox size={48} className="text-slate-500" />}
      </div>
      <h3 className="text-lg font-medium text-slate-300">{title}</h3>
      {description && <p className="mt-2 text-sm text-slate-500 max-w-md">{description}</p>}
    </motion.div>
  );
}
