import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useAuth, isGlobalRole } from '../context/AuthContext';
import karnatakaLogo from '../karnataka_govt_logo.png';

interface SidebarItemProps {
  icon: string;
  label: string;
  isActive?: boolean;
  isCollapsed?: boolean;
  onClick?: () => void;
}

const SidebarItem = ({ icon, label, isActive, isCollapsed, onClick }: SidebarItemProps) => (
  <button
    onClick={onClick}
    title={isCollapsed ? label : undefined}
    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${isCollapsed ? 'justify-center' : ''
      } ${isActive
        ? 'bg-primary-blue/10 text-primary-blue border border-primary-blue/20'
        : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest/50'
      }`}
  >
    <span className="material-symbols-outlined text-2xl shrink-0" style={{ fontVariationSettings: isActive ? "'FILL' 1" : undefined }}>{icon}</span>
    {!isCollapsed && <span className="font-medium text-sm whitespace-nowrap">{label}</span>}
  </button>
);

export const Sidebar = ({
  currentView,
  onNavigate,
  isCollapsed,
  onToggle,
  isMobileOpen,
  onMobileClose,
  onNewCase
}: {
  currentView: string;
  onNavigate: (view: string) => void;
  isCollapsed: boolean;
  onToggle: () => void;
  isMobileOpen?: boolean;
  onMobileClose?: () => void;
  onNewCase?: () => void;
}) => {
  const { user, logout } = useAuth();

  // Close mobile sidebar on route change
  const handleNavigate = (view: string) => {
    onNavigate(view);
    onMobileClose?.();
  };

  // Close mobile sidebar on escape key
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onMobileClose?.();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [onMobileClose]);

  const sidebarContent = (
    <motion.aside
      animate={{ width: isCollapsed ? 72 : 280 }}
      transition={{ duration: 0.25, ease: 'easeInOut' }}
      className="h-screen bg-surface-container/40 backdrop-blur-xl border-r border-outline-variant/20 flex flex-col z-30 overflow-hidden"
    >
      {/* Header with hamburger */}
      <div className={`h-20 flex items-center border-b border-outline-variant/20 ${isCollapsed ? 'px-4 justify-center' : 'px-6 justify-between'}`}>
        {!isCollapsed && (
          <div className="flex items-center gap-3 min-w-0">
            <img
              src={karnatakaLogo}
              alt="Government of Karnataka"
              className="w-10 h-10 shrink-0 rounded-full ring-1 ring-outline-variant/30 shadow-sm bg-white/5 p-0.5"
            />
            <div className="flex flex-col min-w-0 leading-tight">
              <span className="text-xl font-bold text-primary-blue tracking-tight whitespace-nowrap">NyayaDrishti</span>
              <span className="text-[9px] uppercase font-bold text-on-surface-variant tracking-[0.18em] opacity-60 whitespace-nowrap">Govt. of Karnataka</span>
            </div>
          </div>
        )}
        <button
          onClick={onToggle}
          className="p-2 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest/50 transition-all shrink-0 hidden lg:flex"
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <span className="material-symbols-outlined text-xl">menu</span>
        </button>
        {/* Mobile close button */}
        <button
          onClick={onMobileClose}
          className="p-2 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest/50 transition-all shrink-0 lg:hidden"
          title="Close sidebar"
        >
          <span className="material-symbols-outlined text-xl">close</span>
        </button>
      </div>

      <div className={`flex-grow py-6 space-y-1 ${isCollapsed ? 'px-2' : 'px-4'}`}>
        <SidebarItem
          icon="dashboard"
          label="Dashboard"
          isActive={currentView === 'dashboard'}
          isCollapsed={isCollapsed}
          onClick={() => handleNavigate('dashboard')}
        />
        <SidebarItem
          icon="folder_managed"
          label="Cases"
          isActive={currentView === 'cases'}
          isCollapsed={isCollapsed}
          onClick={() => handleNavigate('cases')}
        />
        {/* Execution dashboard — LCO landing page; HLC + global can also view */}
        <SidebarItem
          icon="checklist_rtl"
          label="Execution"
          isActive={currentView === 'execution'}
          isCollapsed={isCollapsed}
          onClick={() => handleNavigate('execution')}
        />
        {/* Deadlines monitor — Nodal Officer landing page; HLC + global can also view */}
        <SidebarItem
          icon="schedule"
          label="Deadlines"
          isActive={currentView === 'deadlines'}
          isCollapsed={isCollapsed}
          onClick={() => handleNavigate('deadlines')}
        />
        {/* Central Law / State Monitoring roles get the cross-department overview */}
        {isGlobalRole(user?.role) && (
          <SidebarItem
            icon="account_tree"
            label="Central View"
            isActive={currentView === 'central-view'}
            isCollapsed={isCollapsed}
            onClick={() => handleNavigate('central-view')}
          />
        )}
        <SidebarItem
          icon="logout"
          label="Logout"
          isCollapsed={isCollapsed}
          onClick={logout}
        />
      </div>


      <div className={`p-4 border-t border-outline-variant/20 flex items-center gap-3 ${isCollapsed ? 'justify-center' : 'px-6'}`}>
        <div className="w-10 h-10 rounded-full bg-primary-blue/20 flex items-center justify-center text-primary-blue font-bold border border-primary-blue/20 uppercase shrink-0">
          {user?.username?.charAt(0) || 'U'}
        </div>
        {!isCollapsed && (
          <div className="overflow-hidden min-w-0">
            <p className="text-on-surface font-semibold text-sm truncate capitalize">{user?.username || 'User'}</p>
            <p className="text-on-surface-variant text-xs truncate">{user?.department_name || (isGlobalRole(user?.role) ? 'All Departments' : 'Legal')}</p>
          </div>
        )}
      </div>
    </motion.aside>
  );

  return (
    <>
      {/* Desktop Sidebar — fixed, always visible */}
      <div className="hidden lg:block fixed left-0 top-0 z-20">
        {sidebarContent}
      </div>

      {/* Mobile Sidebar — overlay drawer */}
      <AnimatePresence>
        {isMobileOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-20 lg:hidden"
              onClick={onMobileClose}
            />
            {/* Drawer */}
            <motion.div
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ duration: 0.25, ease: 'easeInOut' }}
              className="fixed left-0 top-0 z-30 lg:hidden"
            >
              {/* Force expanded on mobile overlay */}
              <motion.aside
                className="h-screen w-[280px] bg-surface-container/95 backdrop-blur-xl border-r border-outline-variant/20 flex flex-col z-30 overflow-hidden"
              >
                {/* Header */}
                <div className="h-20 flex items-center border-b border-outline-variant/20 px-6 justify-between">
                  <div className="flex items-center gap-3 min-w-0">
                    <img
                      src={karnatakaLogo}
                      alt="Government of Karnataka"
                      className="w-10 h-10 shrink-0 rounded-full ring-1 ring-outline-variant/30 shadow-sm bg-white/5 p-0.5"
                    />
                    <div className="flex flex-col min-w-0 leading-tight">
                      <span className="text-xl font-bold text-primary-blue tracking-tight whitespace-nowrap">NyayaDrishti</span>
                      <span className="text-[9px] uppercase font-bold text-on-surface-variant tracking-[0.18em] opacity-60 whitespace-nowrap">Govt. of Karnataka</span>
                    </div>
                  </div>
                  <button
                    onClick={onMobileClose}
                    className="p-2 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest/50 transition-all shrink-0"
                    title="Close sidebar"
                  >
                    <span className="material-symbols-outlined text-xl">close</span>
                  </button>
                </div>

                <div className="flex-grow py-6 space-y-1 px-4">
                  <SidebarItem icon="dashboard" label="Dashboard" isActive={currentView === 'dashboard'} onClick={() => handleNavigate('dashboard')} />
                  <SidebarItem icon="folder_managed" label="Cases" isActive={currentView === 'cases'} onClick={() => handleNavigate('cases')} />
                  <SidebarItem icon="checklist_rtl" label="Execution" isActive={currentView === 'execution'} onClick={() => handleNavigate('execution')} />
                  <SidebarItem icon="schedule" label="Deadlines" isActive={currentView === 'deadlines'} onClick={() => handleNavigate('deadlines')} />
                  {isGlobalRole(user?.role) && (
                    <SidebarItem icon="account_tree" label="Central View" isActive={currentView === 'central-view'} onClick={() => handleNavigate('central-view')} />
                  )}
                  <SidebarItem icon="logout" label="Logout" onClick={logout} />
                </div>

                <div className="p-4 border-t border-outline-variant/20 flex items-center gap-3 px-6">
                  <div className="w-10 h-10 rounded-full bg-primary-blue/20 flex items-center justify-center text-primary-blue font-bold border border-primary-blue/20 uppercase shrink-0">
                    {user?.username?.charAt(0) || 'U'}
                  </div>
                  <div className="overflow-hidden min-w-0">
                    <p className="text-on-surface font-semibold text-sm truncate capitalize">{user?.username || 'User'}</p>
                    <p className="text-on-surface-variant text-xs truncate">{user?.department_name || (isGlobalRole(user?.role) ? 'All Departments' : 'Legal')}</p>
                  </div>
                </div>
              </motion.aside>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
};
