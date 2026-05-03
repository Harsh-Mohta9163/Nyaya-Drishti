import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  size?: number;
  text?: string;
}

export default function LoadingSpinner({ size = 40, text }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      >
        <Loader2 size={size} className="text-blue-400" />
      </motion.div>
      {text && <p className="text-sm text-slate-400">{text}</p>}
    </div>
  );
}
