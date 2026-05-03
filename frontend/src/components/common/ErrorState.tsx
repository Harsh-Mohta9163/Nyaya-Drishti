import { motion } from 'framer-motion';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export default function ErrorState({ message = 'Something went wrong', onRetry }: ErrorStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex flex-col items-center justify-center py-16 text-center"
    >
      <div className="mb-4 rounded-full bg-red-500/10 p-4">
        <AlertCircle size={48} className="text-red-400" />
      </div>
      <h3 className="text-lg font-medium text-slate-300">{message}</h3>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 transition-colors"
        >
          <RefreshCw size={16} />
          Retry
        </button>
      )}
    </motion.div>
  );
}
