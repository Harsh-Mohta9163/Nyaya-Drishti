import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, X, RotateCcw } from 'lucide-react';

interface ConflictAlertProps {
  conflicts: string[];
  onDismiss: () => void;
  onRevert: () => void;
}

export default function ConflictAlert({ conflicts, onDismiss, onRevert }: ConflictAlertProps) {
  if (conflicts.length === 0) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className="rounded-lg bg-amber-500/10 border border-amber-500/30 p-4"
      >
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <AlertTriangle size={18} className="text-amber-400 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-medium text-amber-300">Logical Inconsistency Detected</p>
              <ul className="mt-2 space-y-1">
                {conflicts.map((c, i) => (
                  <li key={i} className="text-xs text-amber-400/80">• {c}</li>
                ))}
              </ul>
            </div>
          </div>
          <button onClick={onDismiss} className="text-amber-400 hover:text-amber-300 transition-colors">
            <X size={16} />
          </button>
        </div>
        <div className="mt-3 flex gap-2">
          <button
            onClick={onRevert}
            className="flex items-center gap-1 rounded-md bg-amber-500/20 px-3 py-1.5 text-xs font-medium text-amber-300 hover:bg-amber-500/30 transition-colors"
          >
            <RotateCcw size={12} /> Revert Changes
          </button>
          <button
            onClick={onDismiss}
            className="rounded-md px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-slate-300 transition-colors"
          >
            Keep Anyway
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
