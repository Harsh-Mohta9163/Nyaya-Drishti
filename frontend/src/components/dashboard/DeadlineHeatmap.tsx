import { useState } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import type { DeadlineItem } from '@/types';
import { useTranslation } from 'react-i18next';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

interface DeadlineHeatmapProps {
  deadlines: DeadlineItem[];
  onCellClick?: (caseId: number) => void;
}

type View = '7d' | '30d' | '90d';

export default function DeadlineHeatmap({ deadlines, onCellClick }: DeadlineHeatmapProps) {
  const [view, setView] = useState<View>('30d');
  const { t } = useTranslation();

  const days = view === '7d' ? 7 : view === '30d' ? 30 : 90;

  const getCellsForView = () => {
    const cells = [];
    const today = new Date();
    for (let i = 0; i < days; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      const dateStr = date.toISOString().split('T')[0];
      const matchingDeadlines = deadlines.filter(d => {
        const daysLeft = d.days_remaining;
        return daysLeft === i;
      });
      cells.push({ date: dateStr, day: date.getDate(), deadlines: matchingDeadlines, index: i });
    }
    return cells;
  };

  const cells = getCellsForView();
  const cols = view === '7d' ? 7 : view === '30d' ? 7 : 10;

  return (
    <Card className="border-border bg-card shadow-sm h-full">
      <CardHeader className="pb-3 border-b border-border/50">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold">{t('dashboard.deadlineHeatmap')}</CardTitle>
          <div className="flex gap-1">
            {(['7d', '30d', '90d'] as View[]).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={cn(
                  'rounded-md px-2.5 py-1 text-xs font-medium transition-colors',
                  view === v
                    ? 'bg-blue-500/20 text-blue-500'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                {v}
              </button>
            ))}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="p-5">
        <div className={cn('grid gap-1', `grid-cols-${cols}`)} style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
          {cells.map((cell) => {
            const urgency = cell.deadlines.length === 0
              ? 'bg-muted/30'
              : cell.deadlines.some(d => d.contempt_risk === 'High')
                ? 'bg-red-500/30 border border-red-500/40'
                : cell.deadlines.some(d => d.contempt_risk === 'Medium')
                  ? 'bg-amber-500/30 border border-amber-500/40'
                  : 'bg-green-500/30 border border-green-500/40';

            return (
              <motion.div
                key={cell.date}
                whileHover={{ scale: 1.15 }}
                onClick={() => cell.deadlines.length > 0 && onCellClick?.(cell.deadlines[0].case_id)}
                className={cn(
                  'aspect-square rounded-md flex items-center justify-center text-[10px] font-medium cursor-pointer transition-colors',
                  urgency,
                  cell.deadlines.length > 0 ? 'text-white' : 'text-muted-foreground/60'
                )}
                title={cell.deadlines.map(d => `${d.case_number} (${d.contempt_risk})`).join(', ') || cell.date}
              >
                {cell.day}
              </motion.div>
            );
          })}
        </div>

        <div className="mt-4 flex items-center gap-4 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-red-500/30 border border-red-500/40" /> High Risk</span>
          <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-amber-500/30 border border-amber-500/40" /> Medium</span>
          <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-green-500/30 border border-green-500/40" /> Low</span>
          <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-muted/30" /> None</span>
        </div>
      </CardContent>
    </Card>
  );
}
