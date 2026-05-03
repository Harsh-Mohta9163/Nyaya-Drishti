import { useState } from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import {
  Clock, AlertTriangle, ClipboardCheck, CheckCircle, ArrowUpCircle, CheckCheck
} from 'lucide-react';
import { mockNotifications } from '@/lib/mockData';
import { cn, formatRelativeTime } from '@/lib/utils';
import type { NotificationType } from '@/types';
import EmptyState from '@/components/common/EmptyState';

const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.06 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

const typeConfig: Record<NotificationType, { icon: React.ReactNode; color: string }> = {
  deadline_warning: { icon: <Clock size={18} />, color: 'text-amber-400 bg-amber-500/10' },
  high_risk_alert: { icon: <AlertTriangle size={18} />, color: 'text-red-400 bg-red-500/10' },
  review_assigned: { icon: <ClipboardCheck size={18} />, color: 'text-blue-400 bg-blue-500/10' },
  case_verified: { icon: <CheckCircle size={18} />, color: 'text-green-400 bg-green-500/10' },
  escalation: { icon: <ArrowUpCircle size={18} />, color: 'text-red-400 bg-red-500/10' },
};

export default function NotificationsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState(mockNotifications);

  const unreadCount = notifications.filter(n => !n.is_read).length;

  const markAllRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
  };

  const handleClick = (notifId: number, caseId: number) => {
    setNotifications(prev => prev.map(n => n.id === notifId ? { ...n, is_read: true } : n));
    navigate(`/cases/${caseId}`);
  };

  // Group by date
  const grouped: Record<string, typeof notifications> = {};
  notifications.forEach(n => {
    const date = new Date(n.created_at).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' });
    if (!grouped[date]) grouped[date] = [];
    grouped[date].push(n);
  });

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      <motion.div variants={item} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">{t('notifications.title')}</h1>
          <p className="text-sm text-slate-400 mt-1">{unreadCount} unread notifications</p>
        </div>
        {unreadCount > 0 && (
          <button
            onClick={markAllRead}
            className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700/50 transition-colors"
          >
            <CheckCheck size={14} />
            {t('notifications.markAllRead')}
          </button>
        )}
      </motion.div>

      {notifications.length === 0 ? (
        <EmptyState title={t('notifications.noNotifications')} />
      ) : (
        Object.entries(grouped).map(([date, notifs]) => (
          <motion.div key={date} variants={item}>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">{date}</p>
            <div className="space-y-2">
              {notifs.map((n) => {
                const config = typeConfig[n.notification_type];
                return (
                  <motion.div
                    key={n.id}
                    whileHover={{ x: 4 }}
                    onClick={() => handleClick(n.id, n.case)}
                    className={cn(
                      'glass-card flex items-start gap-4 p-4 cursor-pointer transition-all',
                      !n.is_read && 'border-l-2 border-l-blue-500'
                    )}
                  >
                    <div className={cn('rounded-lg p-2 shrink-0', config.color)}>
                      {config.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-slate-400">
                          {t(`notifications.${n.notification_type}`)}
                        </span>
                        <span className="text-xs text-blue-400 font-medium">{n.case_number}</span>
                        {!n.is_read && (
                          <span className="h-2 w-2 rounded-full bg-blue-500" />
                        )}
                      </div>
                      <p className="mt-1 text-sm text-slate-300">{n.message}</p>
                      <p className="mt-1 text-[10px] text-slate-600">{formatRelativeTime(n.created_at)}</p>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        ))
      )}
    </motion.div>
  );
}
