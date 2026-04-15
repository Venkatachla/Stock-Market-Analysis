import { BarChart3, TrendingUp, Activity, Wallet, Zap, Newspaper, ChevronLeft, ChevronRight, UserRound, Shield, LineChart, Sigma, ScanSearch } from "lucide-react";
import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useEffect, useMemo, useState } from "react";

const ADVANCED_MODE_KEY = "advanced_mode";

const navItems = [
  { label: "Trade Now", path: "/", icon: BarChart3 },
  { label: "Risk OS", path: "/risk-os", icon: Sigma },
  { label: "Options Lab", path: "/options-lab", icon: ScanSearch },
  { label: "Signals", path: "/signals", icon: Zap },
  { label: "Active Trades", path: "/paper-trading", icon: Wallet },
  { label: "Performance", path: "/performance", icon: LineChart },
  { label: "Control Panel", path: "/admin", icon: Shield },
];

const advancedItems = [
  { label: "Stock Prediction", path: "/stock-prediction", icon: TrendingUp },
  { label: "Backtest", path: "/backtest", icon: Activity },
  { label: "News", path: "/news", icon: Newspaper },
  { label: "Login", path: "/login", icon: UserRound },
];

export function AppSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [advancedMode, setAdvancedMode] = useState(false);

  useEffect(() => {
    const refresh = () => {
      setAdvancedMode(localStorage.getItem(ADVANCED_MODE_KEY) === "true");
    };

    refresh();
    window.addEventListener("advanced-mode-changed", refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener("advanced-mode-changed", refresh);
      window.removeEventListener("storage", refresh);
    };
  }, []);

  const visibleItems = useMemo(() => {
    return advancedMode ? [...navItems, ...advancedItems] : navItems;
  }, [advancedMode]);

  return (
    <aside
      className={cn(
        "h-screen bg-sidebar border-r border-sidebar-border flex flex-col shrink-0 transition-all duration-200",
        collapsed ? "w-16" : "w-56"
      )}
    >
      {/* Logo */}
      <div className="h-14 flex items-center px-4 border-b border-sidebar-border">
        {!collapsed && (
          <span className="text-lg font-bold tracking-tight text-primary">STOCK</span>
        )}
        {collapsed && (
          <span className="text-lg font-bold text-primary mx-auto">S</span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 px-2 space-y-0.5">
        {visibleItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150",
                isActive
                  ? "bg-sidebar-accent text-sidebar-primary"
                  : "text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent/50"
              )
            }
          >
            <item.icon className="h-4.5 w-4.5 shrink-0" />
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
        {!collapsed && !advancedMode && (
          <p className="text-[11px] text-muted-foreground px-3 pt-3">Advanced pages are hidden by default.</p>
        )}
      </nav>

      {/* Collapse toggle */}
      <div className="p-2 border-t border-sidebar-border">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center h-8 rounded-md text-muted-foreground hover:text-foreground hover:bg-sidebar-accent/50 transition-colors"
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>
    </aside>
  );
}