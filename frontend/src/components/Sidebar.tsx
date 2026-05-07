import React from 'react';
import { motion } from 'motion/react';
import { useAuth } from '../context/AuthContext';

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
    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
      isCollapsed ? 'justify-center' : ''
    } ${
      isActive
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
  onToggle
}: { 
  currentView: string; 
  onNavigate: (view: string) => void;
  isCollapsed: boolean;
  onToggle: () => void;
}) => {
  const { user, logout } = useAuth();

  return (
    <motion.aside 
      animate={{ width: isCollapsed ? 72 : 280 }}
      transition={{ duration: 0.25, ease: 'easeInOut' }}
      className="h-screen fixed left-0 top-0 bg-surface-container/40 backdrop-blur-xl border-r border-outline-variant/20 flex flex-col z-20 overflow-hidden"
    >
      {/* Header with hamburger */}
      <div className={`h-20 flex items-center border-b border-outline-variant/20 ${isCollapsed ? 'px-4 justify-center' : 'px-6 justify-between'}`}>
        {!isCollapsed && (
          <div className="flex flex-col min-w-0">
            <span className="text-2xl font-bold text-primary-blue tracking-tight whitespace-nowrap">NyayaDrishti</span>
            <span className="text-[10px] uppercase font-bold text-on-surface-variant tracking-[0.2em] opacity-40 whitespace-nowrap">Legal Intelligence</span>
          </div>
        )}
        <button
          onClick={onToggle}
          className="p-2 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest/50 transition-all shrink-0"
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <span className="material-symbols-outlined text-xl">menu</span>
        </button>
      </div>
      
      <div className={`flex-grow py-6 space-y-1 ${isCollapsed ? 'px-2' : 'px-4'}`}>
        <SidebarItem 
          icon="dashboard" 
          label="Dashboard" 
          isActive={currentView === 'dashboard'} 
          isCollapsed={isCollapsed}
          onClick={() => onNavigate('dashboard')}
        />
        <SidebarItem 
          icon="folder_managed" 
          label="Cases" 
          isActive={currentView === 'cases'} 
          isCollapsed={isCollapsed}
          onClick={() => onNavigate('cases')}
        />
        <SidebarItem 
          icon="logout" 
          label="Logout" 
          isCollapsed={isCollapsed}
          onClick={logout}
        />
      </div>

      <div className={`pb-6 mt-auto ${isCollapsed ? 'px-2' : 'px-6'}`}>
        <button 
          onClick={() => onNavigate('cases')}
          title={isCollapsed ? 'New Case Analysis' : undefined}
          className={`w-full py-3 bg-primary-blue text-on-primary-blue font-bold rounded-lg flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(173,198,255,0.2)] hover:scale-[1.02] active:scale-[0.98] transition-all ${isCollapsed ? 'px-0' : ''}`}
        >
          <span className="material-symbols-outlined">add</span>
          {!isCollapsed && <span className="whitespace-nowrap">New Case Analysis</span>}
        </button>
      </div>

      <div className={`p-4 border-t border-outline-variant/20 flex items-center gap-3 ${isCollapsed ? 'justify-center' : 'px-6'}`}>
        <div className="w-10 h-10 rounded-full bg-primary-blue/20 flex items-center justify-center text-primary-blue font-bold border border-primary-blue/20 uppercase shrink-0">
          {user?.username?.charAt(0) || 'U'}
        </div>
        {!isCollapsed && (
          <div className="overflow-hidden min-w-0">
            <p className="text-on-surface font-semibold text-sm truncate capitalize">{user?.username || 'User'}</p>
            <p className="text-on-surface-variant text-xs truncate capitalize">{user?.department || 'Legal'}</p>
          </div>
        )}
      </div>
    </motion.aside>
  );
};
