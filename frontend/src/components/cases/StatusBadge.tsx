import { cn, statusColor } from '@/lib/utils';
import type { CaseStatus } from '@/types';
import { useTranslation } from 'react-i18next';

interface StatusBadgeProps {
  status: CaseStatus;
  animated?: boolean;
}

export default function StatusBadge({ status, animated = true }: StatusBadgeProps) {
  const { t } = useTranslation();

  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
      statusColor[status]
    )}>
      {animated && status === 'processing' && (
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-400" />
        </span>
      )}
      {t(`status.${status}`)}
    </span>
  );
}
