'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BarChart3, TrendingUp, Activity, PieChart, Target, Settings, LogOut } from 'lucide-react';

export default function Navigation() {
  const pathname = usePathname();

  const menuItems = [
    {
      label: 'Dashboard',
      href: '/',
      icon: BarChart3,
    },
    {
      label: 'Stock Prediction',
      href: '/prediction',
      icon: TrendingUp,
    },
    {
      label: 'Backtest',
      href: '/backtest',
      icon: Activity,
    },
    {
      label: 'Paper Trading',
      href: '/paper-trading',
      icon: PieChart,
    },
    {
      label: 'Signals',
      href: '/signals',
      icon: Target,
    },
  ];

  const isActive = (path: string) => {
    return pathname === path ? 'bg-gray-800/50 border-accent-blue' : '';
  };

  return (
    <div className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-gray-800">
        <h1 className="text-2xl font-bold gradient-text flex items-center gap-2">
          <BarChart3 className="w-6 h-6" />
          STOCK
        </h1>
        <p className="text-xs text-gray-500 mt-1">Quantitative Trading</p>
      </div>

      {/* Menu */}
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg border border-transparent transition-all ${isActive(item.href)} hover:bg-gray-800/30 text-gray-300 hover:text-white`}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800 space-y-2">
        <button className="w-full flex items-center gap-3 px-4 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800/30 transition-all">
          <Settings className="w-5 h-5" />
          <span>Settings</span>
        </button>
        <button className="w-full flex items-center gap-3 px-4 py-2 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-all">
          <LogOut className="w-5 h-5" />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
}
