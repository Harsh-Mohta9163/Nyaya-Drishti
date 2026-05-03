import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, X } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

export default function ServerWakeup() {
  const [show, setShow] = useState(true);
  const { t } = useTranslation();

  useEffect(() => {
    const dismissed = sessionStorage.getItem('server_wakeup_dismissed');
    if (dismissed) setShow(false);
  }, []);

  const dismiss = () => {
    setShow(false);
    sessionStorage.setItem('server_wakeup_dismissed', 'true');
  };

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="overflow-hidden"
        >
          <div className="flex items-center justify-between gap-3 bg-amber-500/10 border-b border-amber-500/20 px-4 py-2.5 text-sm text-amber-300">
            <div className="flex items-center gap-2">
              <AlertTriangle size={16} className="shrink-0" />
              <span>{t('wakeup.banner')}</span>
            </div>
            <button onClick={dismiss} className="shrink-0 hover:text-amber-100 transition-colors">
              <X size={16} />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
