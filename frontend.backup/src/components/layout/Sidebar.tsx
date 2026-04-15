import { Home, LineChart, Sigma, Zap, Bookmark, Settings, ChevronLeft, ChevronRight, Menu, Rocket } from "lucide-react";
import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useState } from "react";

const navItems = [
  { label: "Dashboard", path: "/", icon: Home },
  { label: "AI Scanner", path: "/scanner", icon: Rocket },
  { label: "Options Lab", path: "/options", icon: Sigma },
  { label: "Intraday Alpha", path: "/intraday", icon: Zap },
  { label: "Watchlist", path: "/watchlist", icon: Bookmark },
  { label: "Settings", path: "/settings", icon: Settings },
];

export function Sidebar({ collapsed, setCollapsed }: { collapsed: boolean, setCollapsed: (val: boolean) => void }) {
  return (
    <>
      <aside
        className={cn(
          "hidden md:flex h-screen bg-sidebar border-r border-sidebar-border flex-col shrink-0 transition-all duration-200 sticky top-0",
          collapsed ? "w-16" : "w-64"
        )}
      >
        <div className="h-14 flex items-center justify-between px-4 border-b border-sidebar-border">
          {!collapsed && (
            <span className="text-lg font-bold tracking-tight text-primary">Risk OS</span>
          )}
          {collapsed ? (
            <span className="text-lg font-bold text-primary mx-auto">R</span>
          ) : (
            <button onClick={() => setCollapsed(true)} className="text-muted-foreground hover:text-foreground">
              <ChevronLeft className="h-4 w-4" />
            </button>
          )}
        </div>

        <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-foreground/70 hover:text-foreground hover:bg-muted/50"
                )
              }
              title={collapsed ? item.label : undefined}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
          {collapsed && (
             <button onClick={() => setCollapsed(false)} className="w-full flex justify-center mt-4 text-muted-foreground hover:text-foreground">
               <ChevronRight className="h-4 w-4" />
             </button>
          )}
        </nav>
      </aside>

      {/* Mobile Bottom Nav */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-card border-t border-border z-50 flex items-center justify-around px-2 pb-safe">
        {navItems.slice(0, 5).map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === "/"}
            className={({ isActive }) =>
              cn(
                "flex flex-col items-center justify-center w-full h-full space-y-1",
                isActive ? "text-primary" : "text-muted-foreground"
              )
            }
          >
            <item.icon className="h-5 w-5" />
            <span className="text-[10px] font-medium leading-none">{item.label.split(" ")[0]}</span>
          </NavLink>
        ))}
      </nav>
    </>
  );
}
