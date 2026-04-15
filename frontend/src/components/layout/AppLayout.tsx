import React from 'react';
import { useAppStore } from '@/stores/appStore';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Search, BarChart3, Shield, PieChart,
  Sun, Moon, Menu, X, TrendingUp
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/discovery', label: 'Discovery', icon: Search },
  { path: '/portfolio', label: 'Portfolio', icon: PieChart },
  { path: '/risk', label: 'Risk-OS', icon: Shield },
];

const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { theme, toggleTheme, sidebarOpen, toggleSidebar } = useAppStore();
  const location = useLocation();

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
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default React.memo(AppLayout);
