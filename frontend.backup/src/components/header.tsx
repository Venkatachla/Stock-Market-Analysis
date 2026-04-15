'use client';

import { Bell, Search, Menu } from 'lucide-react';

export default function Header() {
  return (
    <div className="h-16 bg-gray-900/50 border-b border-gray-800 px-6 flex items-center justify-between">
      <div className="flex items-center gap-4 flex-1">
        <div className="hidden md:flex items-center gap-2 flex-1 max-w-md">
          <Search className="w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search stocks..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-accent-blue transition-colors"
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button className="p-2 hover:bg-gray-800 rounded-lg transition-colors relative">
          <Bell className="w-5 h-5 text-gray-400" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-accent-red rounded-full"></span>
        </button>

        <div className="flex items-center gap-3 pl-4 border-l border-gray-800">
          <div>
            <p className="text-sm font-medium text-white">Admin</p>
            <p className="text-xs text-gray-500">Online</p>
          </div>
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent-blue to-accent-purple"></div>
        </div>

        <button className="md:hidden p-2 hover:bg-gray-800 rounded-lg">
          <Menu className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
