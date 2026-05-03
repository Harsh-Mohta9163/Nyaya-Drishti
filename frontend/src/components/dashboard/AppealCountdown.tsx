import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Timer } from 'lucide-react';
import type { DeadlineItem } from '@/types';
import { useTranslation } from 'react-i18next';

interface AppealCountdownProps {
  deadlines: DeadlineItem[];
}

function CountdownTimer({ deadline }: { deadline: string }) {
  const [timeLeft, setTimeLeft] = useState({ days: 0, hours: 0, mins: 0, secs: 0 });

  useEffect(() => {
    const tick = () => {
      const now = new Date().getTime();
      const target = new Date(deadline).getTime();
      const diff = Math.max(0, target - now);
      setTimeLeft({
        days: Math.floor(diff / 86400000),
        hours: Math.floor((diff % 86400000) / 3600000),
        mins: Math.floor((diff % 3600000) / 60000),
        secs: Math.floor((diff % 60000) / 1000),
      });
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [deadline]);

  const units = [
    { label: 'D', value: timeLeft.days },
    { label: 'H', value: timeLeft.hours },
    { label: 'M', value: timeLeft.mins },
    { label: 'S', value: timeLeft.secs },
  ];

  return (
    <div className="flex gap-1.5">
      {units.map(u => (
        <div key={u.label} className="flex flex-col items-center rounded-md bg-slate-800/50 px-2 py-1 min-w-[36px]">
          <span className="text-sm font-bold text-white tabular-nums">{String(u.value).padStart(2, '0')}</span>
          <span className="text-[9px] text-slate-500">{u.label}</span>
        </div>
      ))}
    </div>
  );
}

export default function AppealCountdown({ deadlines }: AppealCountdownProps) {
  const { t } = useTranslation();

  return (
    <div className="glass-card p-5">
      <div className="mb-4 flex items-center gap-2">
        <Timer size={16} className="text-amber-400" />
        <h3 className="text-sm font-semibold text-slate-200">{t('dashboard.appealCountdown')}</h3>
      </div>

      <div className="space-y-3">
        {deadlines.slice(0, 3).map((d, i) => (
          <motion.div
            key={d.case_id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="flex items-center justify-between rounded-lg bg-slate-800/30 px-4 py-3"
          >
            <div>
              <p className="text-sm font-medium text-slate-200">{d.case_number}</p>
              <p className="text-xs text-slate-500">{d.ccms_stage}</p>
            </div>
            <CountdownTimer deadline={d.legal_deadline} />
          </motion.div>
        ))}
      </div>
    </div>
  );
}
