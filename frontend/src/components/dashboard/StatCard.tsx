import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';

interface StatCardProps {
  title: string;
  value: number;
  icon: LucideIcon;
  trend?: { value: number; label: string };
  color?: 'blue' | 'red' | 'amber' | 'green';
  animateCount?: boolean;
}

const colorMap = {
  blue: { bg: 'bg-blue-500/10', text: 'text-blue-500', iconBg: 'bg-blue-500/20' },
  red: { bg: 'bg-red-500/10', text: 'text-red-500', iconBg: 'bg-red-500/20' },
  amber: { bg: 'bg-amber-500/10', text: 'text-amber-500', iconBg: 'bg-amber-500/20' },
  green: { bg: 'bg-green-500/10', text: 'text-green-500', iconBg: 'bg-green-500/20' },
};

export default function StatCard({ title, value, icon: Icon, trend, color = 'blue', animateCount = true }: StatCardProps) {
  const [displayValue, setDisplayValue] = useState(animateCount ? 0 : value);
  const c = colorMap[color];

  useEffect(() => {
    if (!animateCount) return;
    const duration = 1200;
    const steps = 40;
    const increment = value / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= value) {
        setDisplayValue(value);
        clearInterval(timer);
      } else {
        setDisplayValue(Math.floor(current));
      }
    }, duration / steps);
    return () => clearInterval(timer);
  }, [value, animateCount]);

  return (
    <motion.div whileHover={{ scale: 1.02, y: -2 }} transition={{ duration: 0.2 }}>
      <Card className="relative overflow-hidden border-border bg-card shadow-sm hover:shadow-md transition-shadow">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">{title}</p>
              <p className={cn('mt-2 text-3xl font-bold tracking-tight', c.text)}>{displayValue}</p>
              {trend && (
                <p className="mt-1 text-xs text-muted-foreground">
                  <span className={trend.value >= 0 ? 'text-green-500 font-medium' : 'text-red-500 font-medium'}>
                    {trend.value >= 0 ? '+' : ''}{trend.value}%
                  </span>{' '}
                  {trend.label}
                </p>
              )}
            </div>
            <div className={cn('rounded-xl p-3', c.iconBg)}>
              <Icon size={22} className={c.text} />
            </div>
          </div>
          {/* Decorative glow */}
          <div className={cn('absolute -bottom-4 -right-4 h-24 w-24 rounded-full opacity-10 blur-2xl', c.bg)} />
        </CardContent>
      </Card>
    </motion.div>
  );
}
