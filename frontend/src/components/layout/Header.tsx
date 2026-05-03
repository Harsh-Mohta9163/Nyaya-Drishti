import { useTranslation } from 'react-i18next';
import { Bell, Globe, User } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { Link } from 'react-router-dom';
import { mockNotifications } from '@/lib/mockData';

export default function Header() {
  const { i18n } = useTranslation();
  const { user } = useAuth();

  const unreadCount = mockNotifications.filter(n => !n.is_read).length;

  const toggleLanguage = () => {
    const next = i18n.language === 'en' ? 'kn' : 'en';
    i18n.changeLanguage(next);
    localStorage.setItem('language', next);
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border/50 bg-background/80 backdrop-blur-xl px-6">
      <div />

      <div className="flex items-center gap-3">
        {/* Language Toggle */}
        <button
          onClick={toggleLanguage}
          className="flex items-center gap-1.5 rounded-lg border border-border bg-card/50 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-all"
        >
          <Globe size={14} />
          {i18n.language === 'en' ? 'ಕನ್ನಡ' : 'English'}
        </button>

        {/* Notifications */}
        <Link
          to="/notifications"
          className="relative rounded-lg border border-slate-700 bg-slate-800/50 p-2 text-slate-400 hover:bg-slate-700/50 hover:text-white transition-all"
        >
          <Bell size={18} />
          {unreadCount > 0 && (
            <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
              {unreadCount}
            </span>
          )}
        </Link>

        {/* User Avatar */}
        {user && (
          <div className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-1.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-blue-400 to-purple-500">
              <User size={14} className="text-white" />
            </div>
            <span className="text-sm font-medium text-slate-300">{user.username}</span>
          </div>
        )}
      </div>
    </header>
  );
}
