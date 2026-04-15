import { create } from 'zustand';

interface AppState {
  theme: 'dark' | 'light';
  sidebarOpen: boolean;
  refreshInterval: number;
  toggleTheme: () => void;
  toggleSidebar: () => void;
  setRefreshInterval: (ms: number) => void;
}

export const useAppStore = create<AppState>((set) => ({
  theme: 'dark',
  sidebarOpen: true,
  refreshInterval: 30000,
  toggleTheme: () => set((s) => {
    const next = s.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.classList.toggle('dark', next === 'dark');
    return { theme: next };
  }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setRefreshInterval: (ms) => set({ refreshInterval: ms }),
}));

// Initialize dark mode
document.documentElement.classList.add('dark');
