import { cn } from '@/lib/utils';

interface ConfidenceBadgeProps {
  value: number;
  label?: string;
  showPercent?: boolean;
}

export default function ConfidenceBadge({ value, label, showPercent = true }: ConfidenceBadgeProps) {
  const percent = Math.round(value * 100);
  const color = value >= 0.9
    ? 'text-green-400 bg-green-500/10 border-green-500/30'
    : value >= 0.7
      ? 'text-amber-400 bg-amber-500/10 border-amber-500/30'
      : 'text-red-400 bg-red-500/10 border-red-500/30';

  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium', color)}>
      {label && <span>{label}</span>}
      {showPercent && <span>{percent}%</span>}
    </span>
  );
}
