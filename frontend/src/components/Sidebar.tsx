import React from 'react';
import { motion } from 'motion/react';
import { useAuth } from '../context/AuthContext';

interface SidebarItemProps {
  icon: string;
  label: string;
  isActive?: boolean;
  onClick?: () => void;
}

const SidebarItem = ({ icon, label, isActive, onClick }: SidebarItemProps) => (
  <button
    onClick={onClick}
    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
      isActive
        ? 'bg-primary-blue/10 text-primary-blue border border-primary-blue/20'
        : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest/50'
    }`}
  >
    <span className="material-symbols-outlined text-2xl" style={{ fontVariationSettings: isActive ? "'FILL' 1" : undefined }}>{icon}</span>
    <span className="font-medium text-sm">{label}</span>
  </button>
);

export const Sidebar = ({ 
  currentView, 
  onNavigate 
}: { 
  currentView: string; 
  onNavigate: (view: string) => void;
}) => {
  const { user, logout } = useAuth();

  return (
    <aside className="w-[280px] h-screen fixed left-0 top-0 bg-surface-container/40 backdrop-blur-xl border-r border-outline-variant/20 flex flex-col z-20">
      <div className="h-20 flex items-center px-8 border-b border-outline-variant/20">
        <div className="flex flex-col">
          <span className="text-2xl font-bold text-primary-blue tracking-tight">NyayaDrishti</span>
          <span className="text-[10px] uppercase font-bold text-on-surface-variant tracking-[0.2em] opacity-40">Legal Intelligence</span>
        </div>
      </div>
      
      <div className="flex-grow py-6 px-4 space-y-1">
        <SidebarItem 
          icon="dashboard" 
          label="Dashboard" 
          isActive={currentView === 'dashboard'} 
          onClick={() => onNavigate('dashboard')}
        />
        <SidebarItem 
          icon="folder_managed" 
          label="Cases" 
          isActive={currentView === 'cases'} 
          onClick={() => onNavigate('cases')}
        />
        <SidebarItem icon="reviews" label="Reviews" />
        <SidebarItem icon="analytics" label="Analytics" />
        <SidebarItem icon="notifications" label="Notifications" />
        <SidebarItem 
          icon="logout" 
          label="Logout" 
          onClick={logout}
        />
      </div>

      <div className="px-6 pb-6 mt-auto">
        <button 
          onClick={() => onNavigate('cases')}
          className="w-full py-3 bg-primary-blue text-on-primary-blue font-bold rounded-lg flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(173,198,255,0.2)] hover:scale-[1.02] active:scale-[0.98] transition-all"
        >
          <span className="material-symbols-outlined">add</span>
          New Case Analysis
        </button>
      </div>

      <div className="p-6 border-t border-outline-variant/20 flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-primary-blue/20 flex items-center justify-center text-primary-blue font-bold border border-primary-blue/20 uppercase">
          {user?.username?.charAt(0) || 'U'}
        </div>
        <div className="overflow-hidden">
          <p className="text-on-surface font-semibold text-sm truncate capitalize">{user?.username || 'User'}</p>
          <p className="text-on-surface-variant text-xs truncate capitalize">{user?.department || 'Legal'}</p>
        </div>
      </div>
    </aside>
  );
};
