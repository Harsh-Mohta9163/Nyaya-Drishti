import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  glow?: 'blue' | 'red' | 'amber' | 'green' | 'none';
}

const glowColors = {
  blue: 'hover:border-blue-500/50 hover:shadow-[0_0_20px_rgba(59,130,246,0.15)]',
  red: 'hover:border-red-500/50 hover:shadow-[0_0_20px_rgba(239,68,68,0.15)]',
  amber: 'hover:border-amber-500/50 hover:shadow-[0_0_20px_rgba(245,158,11,0.15)]',
  green: 'hover:border-green-500/50 hover:shadow-[0_0_20px_rgba(34,197,94,0.15)]',
  none: '',
};

export default function GlassCard({ children, className, hover = true, glow = 'blue' }: GlassCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'glass-card p-6 lg:p-8',
        hover && 'transition-all duration-200',
        hover && glowColors[glow],
        className
      )}
    >
      {children}
    </motion.div>
  );
}
