import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/context/AuthContext';
import {
  LayoutDashboard, FileText, ClipboardCheck,
  BarChart3, Bell, LogOut, Scale
} from 'lucide-react';
import type { Role } from '@/types';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
  roles: Role[];
}

export default function Sidebar() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();

  const navItems: NavItem[] = [
    { path: '/dashboard', label: t('nav.dashboard'), icon: <LayoutDashboard size={20} />, roles: ['reviewer', 'dept_officer', 'dept_head', 'legal_advisor'] },
    { path: '/cases', label: t('nav.cases'), icon: <FileText size={20} />, roles: ['reviewer', 'dept_officer', 'dept_head', 'legal_advisor'] },
    { path: '/reviews', label: t('nav.reviews'), icon: <ClipboardCheck size={20} />, roles: ['reviewer', 'dept_head', 'legal_advisor'] },
    { path: '/analytics', label: t('nav.analytics'), icon: <BarChart3 size={20} />, roles: ['dept_officer', 'dept_head', 'legal_advisor'] },
    { path: '/notifications', label: t('nav.notifications'), icon: <Bell size={20} />, roles: ['reviewer', 'dept_officer', 'dept_head', 'legal_advisor'] },
  ];

  const filteredItems = navItems.filter(item =>
    user ? item.roles.includes(user.role) : false
  );

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-border/50 bg-card/95 backdrop-blur-xl">
      {/* Logo */}
      <div className="flex items-center gap-3 border-b border-border/50 px-6 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 shadow-lg shadow-blue-500/20">
          <Scale size={20} className="text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-foreground tracking-tight">NyayaDrishti</h1>
          <p className="text-[10px] text-muted-foreground uppercase tracking-widest">CCMS Intelligence</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-1">
          {filteredItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-blue-500/10 text-blue-400 shadow-sm'
                      : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                  }`
                }
              >
                {item.icon}
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* User info + Logout */}
      <div className="border-t border-border/50 p-4">
        {user && (
          <div className="mb-3 rounded-lg bg-muted/30 border border-border/30 p-3">
            <p className="text-sm font-medium text-foreground">{user.username}</p>
            <p className="text-xs text-muted-foreground">{user.department}</p>
            <span className="mt-1 inline-block rounded-full bg-blue-500/10 px-2 py-0.5 text-[10px] font-medium text-blue-400 uppercase">
              {user.role.replace('_', ' ')}
            </span>
          </div>
        )}
        <button
          onClick={logout}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-red-500/10 hover:text-red-400 transition-colors"
        >
          <LogOut size={18} />
          {t('nav.logout')}
        </button>
      </div>
    </aside>
  );
}
