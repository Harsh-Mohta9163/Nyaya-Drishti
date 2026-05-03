import { motion } from 'framer-motion';
import { AlertTriangle, ArrowRight, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { cn, riskColor } from '@/lib/utils';
import type { HighRiskCase } from '@/types';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface RiskBoardProps {
  cases: HighRiskCase[];
}

export default function RiskBoard({ cases }: RiskBoardProps) {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const sorted = [...cases].sort((a, b) => a.days_remaining - b.days_remaining);

  return (
    <Card className="border-border bg-card shadow-sm h-full">
      <CardHeader className="pb-3 border-b border-border/50">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <AlertTriangle size={16} className="text-red-500" />
          {t('dashboard.riskBoard')}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="flex flex-col divide-y divide-border/50">
          {sorted.map((c, i) => (
            <motion.div
              key={c.case_id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.06 }}
              onClick={() => navigate(`/cases/${c.case_id}`)}
              className="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-muted/30 transition-colors group"
            >
              <div className="flex items-center gap-4">
                <div className={cn(
                  'flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-sm font-bold',
                  riskColor[c.contempt_risk]
                )}>
                  {c.days_remaining}d
                </div>
                <div>
                  <p className="text-sm font-semibold text-foreground group-hover:text-blue-400 transition-colors">{c.case_number}</p>
                  <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{c.petitioner}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex flex-col items-end gap-1 hidden sm:flex">
                  <Badge variant="outline" className="text-[10px] font-normal h-5 bg-background">
                    {c.ccms_stage}
                  </Badge>
                  {c.days_remaining <= 7 && (
                    <span className="flex items-center text-[10px] font-medium text-red-500">
                      <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 1.5 }}>
                        <Clock size={10} className="mr-1" />
                      </motion.div>
                      Urgent
                    </span>
                  )}
                </div>
                <ArrowRight size={16} className="text-muted-foreground group-hover:text-blue-400 transition-colors ml-2 shrink-0" />
              </div>
            </motion.div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
