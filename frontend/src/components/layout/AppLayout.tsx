import React from 'react';
import { useAppStore } from '@/stores/appStore';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import {
  LayoutDashboard, Search, BarChart3, Shield, PieChart,
  Sun, Moon, Menu, X, TrendingUp, LogOut, User
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/discovery', label: 'Discovery', icon: Search },
  { path: '/portfolio', label: 'Portfolio', icon: PieChart },
  { path: '/risk', label: 'Risk-OS', icon: Shield },
];

const AppLayout: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const { theme, toggleTheme, sidebarOpen, toggleSidebar } = useAppStore();
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex flex-col border-r border-border bg-card transition-transform duration-300 lg:static lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0 w-60' : '-translate-x-full w-60 lg:w-16 lg:translate-x-0'
        }`}
        aria-label="Main navigation"
      >
        <div className="flex items-center gap-2 px-4 py-4 border-b border-border">
          <TrendingUp className="h-7 w-7 text-primary shrink-0" />
          <span className={`font-bold text-lg text-foreground transition-opacity ${!sidebarOpen ? 'lg:opacity-0 lg:w-0 lg:overflow-hidden' : ''}`}>
            StockPulse
          </span>
        </div>
        <nav className="flex-1 py-4 space-y-1 px-2">
          {navItems.map(({ path, label, icon: Icon }) => {
            const active = location.pathname === path || (path !== '/' && location.pathname.startsWith(path));
            return (
              <Link
                key={path}
                to={path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                  active
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                }`}
                aria-current={active ? 'page' : undefined}
              >
                <Icon className="h-5 w-5 shrink-0" />
                <span className={`${!sidebarOpen ? 'lg:hidden' : ''}`}>{label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="px-3 py-3 border-t border-border space-y-2">
          <button
            onClick={toggleTheme}
            className="flex items-center gap-3 px-3 py-2 rounded-md text-sm text-muted-foreground hover:bg-accent w-full transition-colors"
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            <span className={`${!sidebarOpen ? 'lg:hidden' : ''}`}>
              {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
            </span>
          </button>
          
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2 rounded-md text-sm text-red-400 hover:bg-red-500/10 w-full transition-colors"
            title="Logout"
          >
            <LogOut className="h-5 w-5" />
            <span className={`${!sidebarOpen ? 'lg:hidden' : ''}`}>Logout</span>
          </button>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 bg-background/80 lg:hidden" onClick={toggleSidebar} />
      )}

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="flex items-center gap-3 px-4 py-3 border-b border-border bg-card lg:px-6">
          <button onClick={toggleSidebar} className="text-muted-foreground hover:text-foreground lg:hidden" aria-label="Toggle menu">
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
          <button onClick={toggleSidebar} className="text-muted-foreground hover:text-foreground hidden lg:block" aria-label="Toggle sidebar">
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex-1" />
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className="h-2 w-2 rounded-full bg-signal-buy animate-pulse-gentle" />
              <span>Auto-refresh: 30s</span>
            </div>
            {user && (
              <div className="flex items-center gap-3 pl-4 border-l border-border">
                <div className="text-right hidden sm:block">
                  <p className="text-xs font-medium text-foreground">{user.email}</p>
                  <p className="text-xs text-muted-foreground capitalize">{user.tier}</p>
                </div>
                <div className="w-8 h-8 rounded-full bg-blue-600/20 border border-blue-600/30 flex items-center justify-center">
                  <User className="h-4 w-4 text-blue-400" />
                </div>
              </div>
            )}
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
