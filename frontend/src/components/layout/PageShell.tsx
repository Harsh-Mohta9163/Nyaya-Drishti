import { Outlet, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from './Sidebar';
import Header from './Header';
import ServerWakeup from '@/components/common/ServerWakeup';

export default function PageShell() {
  const location = useLocation();
  return (
    <div className="min-h-screen bg-background text-foreground font-sans dark">
      <Sidebar />
      <div style={{ marginLeft: '16rem', width: 'calc(100% - 16rem)' }} className="flex flex-col min-h-screen">
        <ServerWakeup />
        <Header />
        <main className="flex-1 px-6 py-12 max-w-7xl mx-auto w-full">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.2 }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
